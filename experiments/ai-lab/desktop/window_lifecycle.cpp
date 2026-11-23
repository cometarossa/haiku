/*
 * Independent AI-assisted Haiku research-fork test (MIT License).
 * App_server GUI window creation, concurrent window loops, and teardown.
 * This is a correctness test only, not a native speed benchmark.
 */
#include <Application.h>
#include <OS.h>
#include <Window.h>

#include <stdio.h>
#include <stdlib.h>
#include <vector>

class LifecycleApp : public BApplication {
public:
    LifecycleApp(int batches, int perBatch)
        :
        BApplication("application/x-vnd.cometarossa-HaikuWindowLifecycle"),
        fBatches(batches),
        fPerBatch(perBatch),
        fFailures(0),
        fCompleted(0)
    {
    }

    int Failures() const { return fFailures; }
    int Completed() const { return fCompleted; }

    virtual void ReadyToRun()
    {
        printf("batch,created,closed,failed\n");
        fflush(stdout);
        for (int batch = 0; batch < fBatches; ++batch) {
            std::vector<BWindow*> windows;
            for (int i = 0; i < fPerBatch; ++i) {
                BRect frame(80 + i * 8, 80 + i * 8,
                    240 + i * 8, 170 + i * 8);
                BWindow* window = new BWindow(frame, "Haiku lifecycle probe",
                    B_TITLED_WINDOW, B_NOT_CLOSABLE | B_NOT_ZOOMABLE);
                window->Show();
                windows.push_back(window);
            }

            // Allow app_server to see all concurrent windows in the batch.
            snooze(50000);
            int closed = 0;
            int failed = 0;
            for (size_t i = 0; i < windows.size(); ++i) {
                if (windows[i]->Lock()) {
                    windows[i]->Quit();
                    ++closed;
                    ++fCompleted;
                } else {
                    ++failed;
                    ++fFailures;
                }
            }
            printf("%d,%lu,%d,%d\n", batch + 1,
                (unsigned long)windows.size(), closed, failed);
            fflush(stdout);
        }

        fprintf(stderr,
            "Haiku window lifecycle: batches=%d windows_per_batch=%d"
            " completed=%d failures=%d\n",
            fBatches, fPerBatch, fCompleted, fFailures);
        Quit();
    }

private:
    int fBatches;
    int fPerBatch;
    int fFailures;
    int fCompleted;
};

int
main(int argc, char** argv)
{
    if (argc != 3) {
        fprintf(stderr, "Usage: %s <batches:1..100> <windows-per-batch:1..16>\n",
            argv[0]);
        return 2;
    }
    char* end = NULL;
    long batches = strtol(argv[1], &end, 10);
    if (end == argv[1] || *end != '\0' || batches < 1 || batches > 100)
        return 2;
    end = NULL;
    long perBatch = strtol(argv[2], &end, 10);
    if (end == argv[2] || *end != '\0' || perBatch < 1 || perBatch > 16)
        return 2;

    LifecycleApp app((int)batches, (int)perBatch);
    app.Run();
    return app.Failures() == 0
        && app.Completed() == batches * perBatch ? 0 : 1;
}
