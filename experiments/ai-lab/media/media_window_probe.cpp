/* Independent Haiku lab: read-only persistent scripting probe. MIT license. */
#include <Application.h>
#include <AppDefs.h>
#include <Message.h>
#include <Messenger.h>
#include <OS.h>

#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

struct Window {
    int32 index;
    char title[128];
};

static bool
ReadMap(const char* path, Window* windows, int& count)
{
    FILE* file = fopen(path, "r");
    if (file == NULL)
        return false;
    char line[256];
    count = 0;
    bool ok = true;
    while (fgets(line, sizeof(line), file) != NULL) {
        int index;
        char title[128], extra;
        if (count == 16 || sscanf(line, "%d %127s %c", &index, title, &extra) != 2
            || index < 0 || index >= 64 || strchr(line, '\n') == NULL) {
            ok = false;
            break;
        }
        for (int i = 0; i < count; i++) {
            if (windows[i].index == index || strcmp(windows[i].title, title) == 0)
                ok = false;
        }
        if (!ok)
            break;
        windows[count].index = index;
        strcpy(windows[count++].title, title);
    }
    ok = ok && !ferror(file) && count > 0;
    fclose(file);
    return ok;
}

static status_t
Query(const BMessenger& target, const Window& window, const char* property,
    bigtime_t deadline, BMessage& reply)
{
    BMessage request(B_GET_PROPERTY);
    status_t status = request.AddSpecifier(property);
    if (status == B_OK)
        status = request.AddSpecifier("Window", window.index);
    if (status != B_OK)
        return status;

    // Both delivery and reply waits are bounded. This is not a hard
    // wall-clock deadline under scheduler starvation.
    bigtime_t remaining = deadline - system_time();
    if (remaining < 2)
        return B_TIMED_OUT;
    bigtime_t timeout = remaining / 2;
    if (timeout > 2000000)
        timeout = 2000000;
    status = target.SendMessage(&request, &reply, timeout, timeout);
    if (status != B_OK)
        return status;
    int32 error = B_OK;
    if (reply.FindInt32("error", &error) == B_OK && error != B_OK)
        return error;
    return reply.what == B_REPLY ? B_OK : B_ERROR;
}

int
main(int argc, char** argv)
{
    if (argc != 3) {
        fprintf(stderr, "Usage: %s <index-title-map> <seconds:1..30>\n", argv[0]);
        return 2;
    }
    char* end;
    errno = 0;
    long seconds = strtol(argv[2], &end, 10);
    if (errno != 0 || end == argv[2] || *end != 0 || seconds < 1 || seconds > 30)
        return 2;
    Window windows[16];
    int count;
    if (!ReadMap(argv[1], windows, count))
        return 2;

    bigtime_t start = system_time();
    BApplication app("application/x-vnd.cometarossa-media-window-probe");
    status_t status;
    BMessenger target("application/x-vnd.Haiku-MediaPlayer", -1, &status);
    if (app.InitCheck() != B_OK || status != B_OK || !target.IsValid())
        return 3;
    printf("INIT %" B_PRId64 "\n", system_time() - start);
    start = system_time();
    const bigtime_t deadline = start + seconds * 1000000LL;
    printf("START %" B_PRId64 " %" B_PRId64 " %d\n", start, deadline, count);
    const char* properties[] = {"Title", "IsPlaying", "Position"};
    int attempted = 0;
    int errors = 0;
    for (int sample = 1; sample <= 3; sample++) {
        for (int i = 0; i < count; i++) {
            bool identity = false;
            for (int op = 0; op < 3; op++) {
                if (system_time() >= deadline || (op != 0 && !identity))
                    break;
                BMessage reply;
                bigtime_t before = system_time();
                status = Query(target, windows[i], properties[op], deadline, reply);
                bigtime_t after = system_time();
                int64 value = -1;
                if (status == B_OK) {
                    if (op == 0) {
                        const char* title = NULL;
                        status = reply.FindString("result", &title);
                        if (status == B_OK && strcmp(title, windows[i].title) != 0)
                            status = B_BAD_VALUE;
                        identity = status == B_OK;
                        value = identity;
                    } else if (op == 1) {
                        bool playing = false;
                        status = reply.FindBool("result", &playing);
                        value = playing;
                    } else
                        status = reply.FindInt64("result", &value);
                }
                printf("QUERY %d %" B_PRId32 " %s %" B_PRId64 " %" B_PRId64
                    " %" B_PRId32 " %" B_PRId64 "\n", sample, windows[i].index,
                    properties[op], before, after, status, value);
                fflush(stdout);
                attempted++;
                if (status != B_OK)
                    errors++;
            }
        }
        if (system_time() >= deadline)
            break;
        if (sample != 3) {
            bigtime_t pause = deadline - system_time();
            if (pause > 500000)
                pause = 500000;
            if (pause > 0)
                snooze(pause);
        }
    }
    printf("END %" B_PRId64 " %d %d\n", system_time(), attempted, errors);
    return errors == 0 && attempted == count * 9 ? 0 : 4;
}
