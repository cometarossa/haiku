// AI-assisted independent Haiku research fork. MIT.
// No peer threads, no blocking: measure combined enqueue/dequeue cost.
// The result includes syscall, allocation, locks and payload copies.
#include <OS.h>
#include <cstdio>
#include <cstring>
#include <vector>

static const int kMessages = 4096;

int main()
{
    printf("payload_bytes,batch,repeat,verified,errors,elapsed_us\n");
    for (size_t size : {size_t(0), size_t(64), size_t(4096)}) {
        std::vector<unsigned char> sent(size ? size : 1, 0x5a);
        std::vector<unsigned char> received(sent.size());
        for (int batch : {1, 64}) {
            for (int repeat = 1; repeat <= 3; ++repeat) {
                port_id port = create_port(64, "lab no-block cost");
                if (port < 0) return 2;
                int verified = 0, errors = 0;
                bigtime_t start = system_time();
                for (int i = 0; i < kMessages && !errors; i += batch) {
                    for (int j = 0; j < batch; ++j) {
                        if (write_port_etc(port, i+j, sent.data(), size,
                                B_RELATIVE_TIMEOUT, 0) != B_OK) {
                            ++errors;
                            break;
                        }
                    }
                    for (int j = 0; j < batch && !errors; ++j) {
                        int32 code = -1;
                        ssize_t bytes = read_port_etc(port, &code,
                            received.data(), size, B_RELATIVE_TIMEOUT, 0);
                        if (bytes != (ssize_t)size || code != i+j
                            || memcmp(sent.data(), received.data(), size)) {
                            ++errors;
                            break;
                        }
                        ++verified;
                    }
                }
                bigtime_t elapsed = system_time() - start;
                if (delete_port(port) != B_OK) ++errors;
                printf("%zu,%d,%d,%d,%d,%lld\n", size, batch, repeat,
                    verified, errors, (long long)elapsed);
                if (errors || verified != kMessages) return 1;
            }
        }
    }
    return 0;
}
