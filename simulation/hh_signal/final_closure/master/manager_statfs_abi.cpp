#include <cstddef>
#include <iostream>
#include <sys/vfs.h>
int main() {
  const bool ok = sizeof(long) == 8 && sizeof(struct statfs) == 120 &&
      offsetof(struct statfs, f_fsid) == 56 &&
      offsetof(struct statfs, f_namelen) == 64 &&
      offsetof(struct statfs, f_frsize) == 72 &&
      offsetof(struct statfs, f_flags) == 80;
  std::cout << (ok ? "PASS_LINUX_X86_64_STATFS_ABI_ONLY" : "BLOCKED_STATFS_ABI") << '\n';
  return ok ? 0 : 2;
}
