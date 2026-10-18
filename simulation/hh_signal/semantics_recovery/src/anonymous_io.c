/* Method-only Linux storage bridge. No event encoding, physics or RNG. */
#define _GNU_SOURCE
#include <unistd.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
static dev_t devices[201];
static ino_t inodes[201];
static int recorded[201];
static int leases[201];
int hh_release_unit(int unit) {
    if(unit<0 || unit>200) return -1;
    if(recorded[unit]) close(leases[unit]);
    recorded[unit]=0;
    return 0;
}
int hh_remember_fd(int fd,int unit) {
    struct stat info;
    if(unit<0 || unit>200 || fstat(fd,&info)!=0 || info.st_nlink!=0) return 0;
    /* Hold the reviewed inode alive after a raw Fortran CLOSE. Without this
       lease, immediate inode reuse can make an unrelated scratch look equal. */
    int lease=dup(fd);
    if(lease<0) return 0;
    if(recorded[unit]) close(leases[unit]);
    leases[unit]=lease;
    devices[unit]=info.st_dev;inodes[unit]=info.st_ino;recorded[unit]=1;
    return 1;
}
int hh_reference_fd(void) {
    const char *dir=getenv("TMPDIR");
    if(!dir) return -1;
    char path[4096];
    if(snprintf(path,sizeof path,"%s/hh_method_XXXXXX",dir)>=(int)sizeof path) return -1;
    int fd=mkstemp(path);
    if(fd<0) return -1;
    if(unlink(path)!=0) {close(fd);return -1;}
    return fd;
}
int hh_check_fd(int fd,int unit) {
    char path[80],target[4096];struct stat info;
    snprintf(path,sizeof path,"/proc/self/fd/%d",fd);
    ssize_t n=readlink(path,target,sizeof target-1);
    if(unit<0 || unit>200 || !recorded[unit] || n<0 || fstat(fd,&info)!=0 || !S_ISREG(info.st_mode) || info.st_nlink!=0) return 0;
    if(info.st_dev!=devices[unit] || info.st_ino!=inodes[unit]) return 0;
    target[n]=0;
    return n>=10 && strcmp(target+n-10," (deleted)")==0;
}
int hh_close_fd(int fd) {return close(fd);}
