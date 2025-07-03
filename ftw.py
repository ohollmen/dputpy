import os
import stat

#def my_callback(root, dirs, files):
#    print(f"--- Processing directory: {root} ---")
#    if dirs: print(f"  Subdirectories: {dirs}")
#    if files: print(f"  Files: {files}")
#    # Example: If you wanted to skip traversing a specific subdirectory
#    # if 'temp_data' in dirs:
#    #     dirs.remove('temp_data') # This will prevent os.walk from entering 'temp_data'

# Traverse the filesystem using os.walk and applies a callback.
def ftw(start_path, cb, ctx):
    if not os.path.exists(start_path):
        print(f"Error: Path '{start_path}' does not exist.")
        return
    # https://www.w3schools.com/python/ref_os_lstat.asp
    # sp = {"follow_symlinks": False} # dir_fd=dir_fd
    for root, dirs, files in os.walk(start_path):
        # my_callback(root, dirs, files)
        fst = None
	# Note: Broken symlinks throw/raise an OSError exception (follows symlink) - work around w. lstat() ?
	# os.lstat(path) == os.stat(path, dir_fd=dir_fd, follow_symlinks=False)
	# stat.S_ISREG(file_stat.st_mode)
        for d in dirs: fst = os.stat(f"{root}/{d}", follow_symlinks=False); cb(f"{root}/{d}", fst, ctx)
        for f in files: fst = os.stat(f"{root}/{f}", follow_symlinks=False); cb(f"{root}/{f}", fst, ctx)
        #cb(root, dirs, files) # Never process dir itself ?

def dummytree_create():
  os.makedirs("my_root/dir1/subdirA", exist_ok=True)
  os.makedirs("my_root/dir2", exist_ok=True)
  with open("my_root/file1.txt", "w") as f: f.write("content")
  with open("my_root/dir1/file2.txt", "w") as f: f.write("content")
  with open("my_root/dir1/subdirA/file3.log", "w") as f: f.write("content")

if __name__ == '__main__':
  root = home_dir = os.environ.get('HOME')
  print(f"Starting file tree traversal ({root}):")
  def dummy(path, fst, ctx):
    print(f"Iterating {path} ({fst.st_size} B)");
    if ctx and stat.S_ISREG(fst.st_mode): ctx["fcnt"] += 1
    return
  travctx = {"fcnt": 0}
  ftw(root, dummy, travctx)
  print(f"Traversed {travctx['fcnt']} files.")
  #ftw(root, my_callback) # Old sign !
# Clean up dummy files/directories
# import shutil
# shutil.rmtree("my_root")
