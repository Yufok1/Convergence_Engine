import os
import sys
import tempfile
import threading
import time
import psutil
import win32job
import win32process
import win32con
import subprocess

class IsolatedChamber:
    def __init__(self, timeout_sec=2, mem_limit_mb=64, cpu_time_sec=2):
        self.timeout_sec = timeout_sec
        self.mem_limit_mb = mem_limit_mb
        self.cpu_time_sec = cpu_time_sec
        self.chamber_dir = tempfile.mkdtemp(prefix="chamber_")

    def _run_in_job(self, command):
        # Create a job object for resource limits
        job = win32job.CreateJobObject(None, "ChamberJob")
        limits = win32job.QueryInformationJobObject(job, win32job.JobObjectExtendedLimitInformation)
        limits['ProcessMemoryLimit'] = self.mem_limit_mb * 1024 * 1024
        limits['BasicLimitInformation']['PerProcessUserTimeLimit'] = self.cpu_time_sec * 10000000  # 100ns units
        limits['BasicLimitInformation']['LimitFlags'] |= win32job.JOB_OBJECT_LIMIT_PROCESS_MEMORY | win32job.JOB_OBJECT_LIMIT_PROCESS_TIME
        win32job.SetInformationJobObject(job, win32job.JobObjectExtendedLimitInformation, limits)

        # Start the process in the chamber directory
        proc = subprocess.Popen(
            command,
            cwd=self.chamber_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True
        )
        win32job.AssignProcessToJobObject(job, proc._handle)
        return proc, job

    def run(self, command):
        """
        Run an untrusted command in the isolated chamber with enforced timeouts and resource quotas.
        Returns (stdout, stderr, timed_out, resource_exceeded)
        """
        proc, job = self._run_in_job(command)
        timed_out = False
        resource_exceeded = False
        output = {'stdout': b'', 'stderr': b''}
        def target():
            try:
                out, err = proc.communicate(timeout=self.timeout_sec)
                output['stdout'], output['stderr'] = out, err
            except subprocess.TimeoutExpired:
                nonlocal timed_out
                timed_out = True
                proc.kill()
        thread = threading.Thread(target=target)
        thread.start()
        thread.join(self.timeout_sec + 1)
        if thread.is_alive():
            timed_out = True
            proc.kill()
            thread.join()
        # Check resource usage
        try:
            p = psutil.Process(proc.pid)
            mem = p.memory_info().rss
            cpu = p.cpu_times().user
            if mem > self.mem_limit_mb * 1024 * 1024 or cpu > self.cpu_time_sec:
                resource_exceeded = True
                proc.kill()
        except Exception:
            pass
        stdout, stderr = output['stdout'], output['stderr']
        return stdout, stderr, timed_out, resource_exceeded

    def cleanup(self):
        try:
            for f in os.listdir(self.chamber_dir):
                os.remove(os.path.join(self.chamber_dir, f))
            os.rmdir(self.chamber_dir)
        except Exception:
            pass

# Example usage:
if __name__ == "__main__":
    chamber = IsolatedChamber(timeout_sec=2, mem_limit_mb=32, cpu_time_sec=1)
    # Example: run a simple Python script
    with open(os.path.join(chamber.chamber_dir, "test.py"), "w") as f:
        f.write("while True: pass\n")
    out, err, timed_out, resource_exceeded = chamber.run("python test.py")
    print("Timed out:", timed_out, "Resource exceeded:", resource_exceeded)
    chamber.cleanup()
