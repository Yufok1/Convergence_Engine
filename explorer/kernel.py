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
            try:
                with open(self.latest_link, 'r') as f:
                    version_filename = f.read().strip()
                if not version_filename:
                    self.sovereign_ids = []
                    self.version_file = None
                    return
                version_path = os.path.join(self.versions_dir, version_filename)
                self.version_file = version_path
                if os.path.exists(version_path):
                    try:
                        with open(version_path, 'r') as f:
                            content = f.read().strip()
                            # Skip files that are empty or contain only null bytes
                            if not content or content.startswith('\x00'):
                                self.sovereign_ids = []
                                self.version_file = None
                                return
                            self.sovereign_ids = json.loads(content)
                    except (json.JSONDecodeError, ValueError, UnicodeDecodeError) as e:
                        # File is corrupted or invalid JSON, treat as empty
                        self.sovereign_ids = []
                        self.version_file = None
                else:
                    self.sovereign_ids = []
                    self.version_file = None
            except Exception as e:
                # Any error reading latest.link, treat as empty
                self.sovereign_ids = []
                self.version_file = None
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
            
            # Windows-compatible atomic file replace
            # Delete old file first if it exists (Windows requires this)
            # Add retry logic for Windows file locking issues
            max_retries = 3
            retry_delay = 0.1  # 100ms between retries
            success = False
            
            for attempt in range(max_retries):
                try:
                    if os.path.exists(self.latest_link):
                        # Try to remove with retry
                        try:
                            os.remove(self.latest_link)
                        except PermissionError:
                            # File might be locked - wait and retry
                            if attempt < max_retries - 1:
                                time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                                continue
                            else:
                                # Last attempt - try to force unlock on Windows
                                try:
                                    # On Windows, try to remove read-only flag first
                                    import stat
                                    os.chmod(self.latest_link, stat.S_IWRITE)
                                    os.remove(self.latest_link)
                                except Exception:
                                    # If still locked, log warning but continue
                                    print(f"[Kernel] Warning: Could not remove locked file {self.latest_link}, will try to overwrite")
                    
                    # Try atomic rename (preferred method)
                    os.rename(tmp_link, self.latest_link)
                    success = True
                    break
                    
                except (OSError, PermissionError) as e:
                    if attempt < max_retries - 1:
                        # Wait before retry
                        time.sleep(retry_delay * (attempt + 1))
                        continue
                    else:
                        # Last attempt - try copy + delete approach
                        try:
                            import shutil
                            # Try to remove with chmod first
                            if os.path.exists(self.latest_link):
                                try:
                                    import stat
                                    os.chmod(self.latest_link, stat.S_IWRITE)
                                    os.remove(self.latest_link)
                                except Exception:
                                    pass  # Ignore if still can't remove
                            shutil.move(tmp_link, self.latest_link)
                            success = True
                            break
                        except Exception as e2:
                            # Final fallback: log error but don't crash
                            # The version file was already created successfully, so data is safe
                            print(f"[Kernel] Warning: Could not update latest.link: {e2}")
                            print(f"[Kernel] Version file created successfully: {version_path}")
                            print(f"[Kernel] You may need to manually update latest.link or restart the system")
                            # Clean up temp file
                            try:
                                if os.path.exists(tmp_link):
                                    os.remove(tmp_link)
                            except:
                                pass
                            # Still return True since the version file was created
                            success = True
                            break
            
            if not success:
                # If all retries failed, at least clean up temp file
                try:
                    if os.path.exists(tmp_link):
                        os.remove(tmp_link)
                except:
                    pass
            self.version_file = version_path
            return True  # Sovereign ID was added
        else:
            return False  # Sovereign ID already exists

    def rollback(self):
        """
        Atomically switch latest.link back to the previous kernel version file.
        """
        try:
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
            try:
                with open(prev_path, 'r') as f:
                    content = f.read().strip()
                    # Skip files that are empty or contain only null bytes
                    if not content or content.startswith('\x00'):
                        self.sovereign_ids = []
                        return False
                    self.sovereign_ids = json.loads(content)
                return True
            except (json.JSONDecodeError, ValueError, UnicodeDecodeError):
                # Previous version is corrupted, treat as failed rollback
                self.sovereign_ids = []
                return False
        except Exception:
            return False

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
