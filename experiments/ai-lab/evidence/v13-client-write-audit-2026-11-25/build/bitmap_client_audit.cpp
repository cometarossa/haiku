// AI-assisted independent research fork. MIT.
// Positive control requires interception of the actual BBitmap memset.
#include <Application.h>
#include <Bitmap.h>
#include <dlfcn.h>
#include <cstdio>
#include <cstring>

typedef int (*Begin)();
typedef int (*Finish)(const void*);

int main(int argc,char** argv)
{
    if (argc != 3) return 2;
    bool lab = strcmp(argv[1],"lab")==0;
    if (!lab && strcmp(argv[1],"ordinary")!=0) return 2;
    bool skip = strcmp(argv[2],"single")==0 || strcmp(argv[2],"quiet")==0;
    if (!skip && strcmp(argv[2],"off")!=0 && strcmp(argv[2],"warm")!=0) return 2;
    int expected = lab && skip ? 0 : 1;
    BApplication app(lab ? "application/x-vnd.cometarossa-v11-client-audit"
        : "application/x-vnd.cometarossa-ordinary-client-audit");
    if (app.InitCheck()!=B_OK) return 3;
    Begin begin = reinterpret_cast<Begin>(dlsym(RTLD_DEFAULT,"bitmap_audit_begin"));
    Finish finish = reinterpret_cast<Finish>(dlsym(RTLD_DEFAULT,"bitmap_audit_finish"));
    if (!begin || !finish || begin()!=0) return 4;
    BBitmap bitmap(BRect(0,0,255,255),
        B_BITMAP_ACCEPTS_VIEWS | B_BITMAP_CLEAR_TO_WHITE,B_RGB32);
    const void* bits = bitmap.Bits();
    int hits = finish(bits);
    if (bitmap.InitCheck()!=B_OK || !bits || bitmap.BitsLength()!=262144) return 5;
    unsigned bad=0;
    const unsigned char* bytes=static_cast<const unsigned char*>(bits);
    for (unsigned i=0;i<262144;++i) if (bytes[i]!=255) ++bad;
    printf("%d,%d,262144,%u\n",expected,hits,bad);
    return hits==expected && bad==0 ? 0 : 6;
}
