#include <windows.h>

#define OWN_INPUT_TAG 0x43414D41

__declspec(dllexport) long long __cdecl counter_frequency(void) {
    LARGE_INTEGER frequency;
    QueryPerformanceFrequency(&frequency);
    return frequency.QuadPart;
}

static void add_key(INPUT *events, int *count, WORD key, DWORD flags) {
    INPUT *event = &events[(*count)++];
    ZeroMemory(event, sizeof(*event));
    event->type = INPUT_KEYBOARD;
    event->ki.wVk = key;
    event->ki.dwFlags = flags;
    event->ki.dwExtraInfo = OWN_INPUT_TAG;
}

static BOOL is_trigger_modifier(WORD modifier, WORD trigger) {
    if (modifier == trigger) return TRUE;
    if (trigger == VK_SHIFT && (modifier == VK_LSHIFT || modifier == VK_RSHIFT)) return TRUE;
    if (trigger == VK_CONTROL && (modifier == VK_LCONTROL || modifier == VK_RCONTROL)) return TRUE;
    if (trigger == VK_MENU && (modifier == VK_LMENU || modifier == VK_RMENU)) return TRUE;
    return FALSE;
}

static BOOL is_modifier(WORD key) {
    return key == VK_SHIFT || key == VK_CONTROL || key == VK_MENU ||
           key == VK_LSHIFT || key == VK_RSHIFT || key == VK_LCONTROL ||
           key == VK_RCONTROL || key == VK_LMENU || key == VK_RMENU ||
           key == VK_LWIN || key == VK_RWIN;
}

// Output keys are held together, then released in reverse order.
__declspec(dllexport) int __cdecl send_keys(const WORD *keys, unsigned int key_count,
                                            unsigned short trigger_vk, long long *entry_ticks) {
    LARGE_INTEGER count;
    QueryPerformanceCounter(&count);
    if (entry_ticks) *entry_ticks = count.QuadPart;
    if (!keys || key_count == 0 || key_count > 8) return 0;

    const WORD modifiers[] = {VK_LSHIFT, VK_RSHIFT, VK_LCONTROL, VK_RCONTROL,
                              VK_LMENU, VK_RMENU, VK_LWIN, VK_RWIN};
    BOOL held[8] = {0};
    WORD ordered[8];
    unsigned int ordered_count = 0;
    INPUT events[32];
    int used = 0;
    for (int i = 0; i < 8; ++i) {
        held[i] = (GetAsyncKeyState(modifiers[i]) & 0x8000) != 0;
        if (held[i]) add_key(events, &used, modifiers[i], KEYEVENTF_KEYUP);
    }
    for (unsigned int i = 0; i < key_count; ++i)
        if (is_modifier(keys[i])) ordered[ordered_count++] = keys[i];
    for (unsigned int i = 0; i < key_count; ++i)
        if (!is_modifier(keys[i])) ordered[ordered_count++] = keys[i];
    for (unsigned int i = 0; i < ordered_count; ++i)
        add_key(events, &used, ordered[i], 0);
    for (int i = (int)ordered_count - 1; i >= 0; --i)
        add_key(events, &used, ordered[i], KEYEVENTF_KEYUP);
    for (int i = 0; i < 8; ++i) {
        if (held[i] && !is_trigger_modifier(modifiers[i], trigger_vk))
            add_key(events, &used, modifiers[i], 0);
    }
    return SendInput((UINT)used, events, sizeof(INPUT)) == (UINT)used;
}
