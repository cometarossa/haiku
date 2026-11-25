// AI-assisted independent research fork. MIT.
// Diagnostic-only LD_PRELOAD interposer, never use for timing.
#include <stddef.h>
#include <dlfcn.h>
#include <stdint.h>

typedef void* (*Fill)(void*, int, size_t);
static thread_local Fill realFill = nullptr;
static thread_local bool armed = false;
static thread_local bool overflow = false;
static thread_local unsigned count = 0;
static thread_local const void* destinations[128];

extern "C" int bitmap_audit_begin()
{
    if (armed) return -1;
    realFill = reinterpret_cast<Fill>(dlsym(RTLD_NEXT,"memset"));
    if (!realFill) return -2;
    count = 0;
    overflow = false;
    armed = true;
    return 0;
}

extern "C" int bitmap_audit_finish(const void* target)
{
    if (!armed || target == nullptr) return -1;
    armed = false;
    if (overflow) return -2;
    int hits = 0;
    for (unsigned i=0; i<count; ++i)
        if (destinations[i] == target) ++hits;
    return hits;
}

extern "C" __attribute__((noinline))
void* memset(void* ptr, int value, size_t length) noexcept
{
    if (armed && length == 262144 && (value & 255) == 255) {
        if (count < 128) destinations[count++] = ptr;
        else overflow = true;
    }
    // Startup calls may precede audit_begin. Volatile writes prevent
    // compiler recognition of this fallback as a recursive memset.
    Fill fill = realFill;
    if (fill && fill != &memset) return fill(ptr,value,length);
    volatile unsigned char* bytes = static_cast<volatile unsigned char*>(ptr);
    for (size_t i=0; i<length; ++i) bytes[i] = (unsigned char)value;
    return ptr;
}
