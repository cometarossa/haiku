// AI-assisted independent Haiku research fork. MIT.
// Test an unreadable userspace buffer in this process only.
#include <OS.h>
#include <sys/mman.h>
#include <cstdio>
int main()
{
    port_id port = create_port(1, "lab copy error");
    if (port < 0) return 2;
    void* buffer = mmap(NULL, B_PAGE_SIZE, PROT_NONE,
        MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (buffer == MAP_FAILED) { delete_port(port); return 3; }
    status_t bad = write_port_etc(port, 42, buffer, 1,
        B_RELATIVE_TIMEOUT, 100000);
    int32 code = 0;
    char value = 0;
    ssize_t empty = read_port_etc(port, &code, &value, 1,
        B_RELATIVE_TIMEOUT, 0);
    char sent = 'X';
    status_t good = write_port_etc(port, 43, &sent, 1,
        B_RELATIVE_TIMEOUT, 100000);
    ssize_t read = read_port_etc(port, &code, &value, 1,
        B_RELATIVE_TIMEOUT, 100000);
    bool recovered = good == B_OK && read == 1 && code == 43 && value == sent;
    bool pass = bad == B_BAD_ADDRESS && empty == B_WOULD_BLOCK && recovered;
    printf("bad_status,expected_bad_address,empty_status,expected_would_block,recovered,pass\n");
    printf("%ld,%ld,%ld,%ld,%d,%d\n",(long)bad,(long)B_BAD_ADDRESS,
        (long)empty,(long)B_WOULD_BLOCK,int(recovered),int(pass));
    munmap(buffer, B_PAGE_SIZE);
    delete_port(port);
    return pass ? 0 : 1;
}
