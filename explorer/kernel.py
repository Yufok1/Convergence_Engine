import os
import json
import shutil
import time

class Kernel:
    def __init__(self, kernel_dir='data/kernel', link_name='latest.link'):
        self.kernel_dir = os.path.abspath(kernel_dir)
        self.versions_dir = os.path.join(self.kernel_dir, 'versions')
        self.latest_link = os.path.join(self.kernel_dir, link_name)
        # Ensure directories exist
        os.makedirs(self.kernel_dir, exist_ok=True)
        os.makedirs(self.versions_dir, exist_ok=True)
        self.sovereign_ids = []
        self.version_file = None
        self._load_state()

    def _load_state(self):
        if os.path.exists(self.latest_link):
            with open(self.latest_link, 'r') as f:
                version_filename = f.read().strip()
            version_path = os.path.join(self.versions_dir, version_filename)
            self.version_file = version_path
            if os.path.exists(version_path):
                with open(version_path, 'r') as f:
                    self.sovereign_ids = json.load(f)
        else:
            self.sovereign_ids = []
            self.version_file = None

    def amend(self, new_sovereign_id):
        """
        Add a new certified function sovereign ID to the kernel and create a new version.
        Atomically update latest.link to point to the new version file.
        """
        # Only add if sovereign ID is not already present (deduplication)
        if new_sovereign_id not in self.sovereign_ids:
            # Ensure versions directory exists
            os.makedirs(self.versions_dir, exist_ok=True)
            
            self.sovereign_ids.append(new_sovereign_id)
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            version_filename = f'kernel_{timestamp}.json'
            version_path = os.path.join(self.versions_dir, version_filename)
            with open(version_path, 'w') as f:
                json.dump(self.sovereign_ids, f)
            # Atomically update latest.link as a text file
            tmp_link = self.latest_link + '.tmp'
            with open(tmp_link, 'w') as f:
                f.write(version_filename)
            os.replace(tmp_link, self.latest_link)
            self.version_file = version_path
            return True  # Sovereign ID was added
        else:
            return False  # Sovereign ID already exists

    def rollback(self):
        """
        Atomically switch latest.link back to the previous kernel version file.
        """
        # Find previous version file
        versions = sorted(os.listdir(self.versions_dir))
        if len(versions) < 2:
            return False  # No previous version to roll back to
        prev_version = versions[-2]
        prev_path = os.path.join(self.versions_dir, prev_version)
        # Atomically update latest.link as a text file
        tmp_link = self.latest_link + '.tmp'
        with open(tmp_link, 'w') as f:
            f.write(prev_version)
        os.replace(tmp_link, self.latest_link)
        self.version_file = prev_path
        with open(prev_path, 'r') as f:
            self.sovereign_ids = json.load(f)
        return True

    def get_sovereign_ids(self):
        return list(self.sovereign_ids)

# Example usage:
if __name__ == "__main__":
    kernel = Kernel()
    print("Current Sovereign IDs:", kernel.get_sovereign_ids())
    kernel.amend("hash-1234567890abcdef")
    print("After amendment:", kernel.get_sovereign_ids())
    kernel.rollback()
    print("After rollback:", kernel.get_sovereign_ids())
