// AI-assisted independent Haiku research fork. MIT.
// Raw reply probe; never writes to shared bitmap memory.
#include <Application.h>
#include <Bitmap.h>
#include <OS.h>
#include <AppServerLink.h>
#include <ServerProtocol.h>
#include <cstdio>
#include <cstring>

using namespace BPrivate;

// Deliberate literal independent of the new server/client enum.
static const uint8 kExpectedAllocator = 0x01;
static const uint8 kExpectedAck = 0x08;
static const uint8 kExpectedQuiet = 0x10;

static status_t DeleteBitmap(int32 token)
{
    AppServerLink link;
    if (link.StartMessage(AS_DELETE_BITMAP) != B_OK
        || link.Attach<int32>(token) != B_OK)
        return B_ERROR;
    return link.Flush(5000000);
}

static int Probe(uint8 expected, bool white)
{
    const BRect bounds(0,0,255,255);
    const int32 stride = 1024;
    const size_t length = 262144;
    const uint32 flags = B_BITMAP_ACCEPTS_VIEWS | B_BITMAP_CLEAR_TO_WHITE;
    int32 token = -1, reply = B_ERROR;
    uint8 received = 0;
    area_id serverArea = -1;
    ssize_t offset = -1;
    {
        AppServerLink link;
        if (link.StartMessage(AS_CREATE_BITMAP) != B_OK
            || link.Attach<BRect>(bounds) != B_OK
            || link.Attach<color_space>(B_RGB32) != B_OK
            || link.Attach<uint32>(flags) != B_OK
            || link.Attach<int32>(stride) != B_OK
            || link.Attach<int32>(0) != B_OK
            || link.Flush(5000000, true) != B_OK
            || link.GetNextMessage(reply,5000000) != B_OK
            || reply != B_OK
            || link.Read<int32>(&token) != B_OK || token < 0
            || link.Read<uint8>(&received) != B_OK
            || link.Read<area_id>(&serverArea) != B_OK
            || link.Read<ssize_t>(&offset) != B_OK)
            return 3;
    }

    int result = 0;
    size_t checked = 0, bad = 0;
    if (received != expected || serverArea < 0 || offset < 0)
        result = 4;
    else if (white) {
        void* base = NULL;
        area_id local = clone_area("lab reply read-only", &base,
            B_ANY_ADDRESS, B_READ_AREA, serverArea);
        if (local < 0)
            result = 5;
        else {
            area_info info;
            if (get_area_info(local, &info) != B_OK
                || base == NULL || info.address != base
                || (size_t)offset > info.size
                || length > info.size - (size_t)offset)
                result = 6;
            else {
                const uint8* bytes = static_cast<const uint8*>(base) + offset;
                for (size_t i = 0; i < length; ++i) {
                    ++checked;
                    if (bytes[i] != 255) ++bad;
                }
                if (bad != 0) result = 7;
            }
            if (delete_area(local) != B_OK) result = 8;
        }
    }
    if (DeleteBitmap(token) != B_OK) result = 9;
    printf("%u,%u,%zu,%zu,%d\n",(unsigned)expected,(unsigned)received,
        checked,bad,result);
    return result;
}

int main(int argc,char** argv)
{
    if (argc != 3) return 2;
    const bool lab = strcmp(argv[1],"lab") == 0;
    if (!lab && strcmp(argv[1],"ordinary") != 0) return 2;
    uint8 expected = kExpectedAllocator;
    bool white = false;
    if (strcmp(argv[2],"off") == 0) {}
    else if (strcmp(argv[2],"warm") == 0) white = lab;
    else if (strcmp(argv[2],"single") == 0) {
        if (lab) expected |= kExpectedAck;
        white = lab;
    } else if (strcmp(argv[2],"quiet") == 0) {
        if (lab) expected |= kExpectedAck | kExpectedQuiet;
        white = lab;
    } else return 2;
    BApplication app(lab ? "application/x-vnd.cometarossa-v11-reply-probe"
        : "application/x-vnd.cometarossa-ordinary-reply-probe");
    if (app.InitCheck() != B_OK) return 10;
    return Probe(expected,white);
}
