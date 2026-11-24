// AI-assisted independent Haiku research fork. MIT.
// Guest-only helper; callers must restore the original scheduler mode.
#include <OS.h>
#include <scheduler.h>
#include <cstdio>
#include <cstring>
int main(int argc,char** argv)
{
    if(argc==2) {
        if(strcmp(argv[1],"0") && strcmp(argv[1],"1")) return 2;
        int mode=argv[1][0]-'0';
        if(set_scheduler_mode(mode)!=B_OK || get_scheduler_mode()!=mode) return 3;
    } else if(argc!=1) return 2;
    int mode=get_scheduler_mode();
    if(mode!=0 && mode!=1) return 4;
    printf("%d\n",mode);
    return 0;
}
