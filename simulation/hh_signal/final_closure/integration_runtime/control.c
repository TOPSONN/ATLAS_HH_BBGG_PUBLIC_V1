#define _GNU_SOURCE
#include <fcntl.h>
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/stat.h>
/* This capability proves supervision, not human approval. The trusted operator
   must separately obtain approval of the exact executable revision. */
int hi_check_parent(int64_t seed) {
    const char *raw=getenv("HH_SUPERVISOR_FD");
    char buffer[512],magic[64],contract[80],revision[80];
    long parent;long long expected;
    if(!raw) return 0;
    int fd=atoi(raw),seals=fcntl(fd,F_GET_SEALS);
    int required=F_SEAL_SEAL|F_SEAL_SHRINK|F_SEAL_GROW|F_SEAL_WRITE;
    struct stat info;
    if(fd<3 || seals<0 || (seals&required)!=required ||
       fstat(fd,&info)!=0 || info.st_nlink!=0 || !S_ISREG(info.st_mode)) return 0;
    ssize_t n=pread(fd,buffer,sizeof(buffer)-1,0);
    if(n<=0) return 0;
    buffer[n]=0;
    if(sscanf(buffer,"%63s %ld %lld %79s %79s",magic,&parent,&expected,contract,revision)!=5) return 0;
    return strcmp(magic,"HH_FINAL_SUPERVISED_V1")==0 && parent==getppid() &&
       expected==seed && strlen(revision)==40 &&
       strcmp(contract,"a8a093e2ec47283dd9cb503b2c83fe95b89df4761df5fb7afc623fa291c937cb")==0;
}
