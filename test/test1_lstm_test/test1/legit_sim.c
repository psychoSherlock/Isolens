#define _WIN32_WINNT 0x0601
#include <winsock2.h>
#include <ws2tcpip.h>
#include <windows.h>
#include <stdio.h>

#pragma comment(lib, "ws2_32.lib")

int main() {
    printf("[*] Starting Legitimate Calculator/Utility Process (PID: %lu)...\n", GetCurrentProcessId());

    // 1. Query System Timing & Metrics (Standard Benign Telemetry)
    DWORD ticks = GetTickCount();
    SYSTEMTIME st;
    GetLocalTime(&st);
    printf("[+] System Time: %02d:%02d:%02d, Uptime Ticks: %lu\n", st.wHour, st.wMinute, st.wSecond, ticks);

    // 2. Read Benign Registry Setting (Read-Only access to Desktop Theme setting)
    HKEY hKey;
    const wchar_t* subKey = L"Control Panel\\Desktop";
    if (RegOpenKeyExW(HKEY_CURRENT_USER, subKey, 0, KEY_READ, &hKey) == ERROR_SUCCESS) {
        wchar_t buffer[256];
        DWORD bufSize = sizeof(buffer);
        DWORD type = 0;
        if (RegQueryValueExW(hKey, L"WallPaper", NULL, &type, (LPBYTE)buffer, &bufSize) == ERROR_SUCCESS) {
            printf("[+] Read user desktop wallpaper configuration successfully.\n");
        }
        RegCloseKey(hKey);
    }

    // 3. Read an Existing System DLL in Read-Only Mode
    const wchar_t* sysPath = L"C:\\Windows\\System32\\kernel32.dll";
    HANDLE hFile = CreateFileW(
        sysPath,
        GENERIC_READ,
        FILE_SHARE_READ,
        NULL,
        OPEN_EXISTING,
        FILE_ATTRIBUTE_NORMAL,
        NULL
    );
    if (hFile != INVALID_HANDLE_VALUE) {
        char header[64];
        DWORD readBytes = 0;
        if (ReadFile(hFile, header, sizeof(header), &readBytes, NULL)) {
            printf("[+] Read %lu bytes from system library %ls\n", readBytes, sysPath);
        }
        CloseHandle(hFile);
    }

    // 4. Benign calculation / processing
    long long total = 0;
    for (int i = 0; i < 100000; i++) {
        total += (i % 7);
    }
    printf("[+] Computation completed (checksum: %lld)\n", total);

    // 5. Standard Legitimate Network Sync Query (NTP time check query)
    WSADATA wsaData;
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) == 0) {
        const char* timeServer = "time.windows.com";
        printf("[+] Checking standard time server: %s\n", timeServer);
        struct addrinfo hints, *res = NULL;
        ZeroMemory(&hints, sizeof(hints));
        hints.ai_family = AF_INET;
        hints.ai_socktype = SOCK_DGRAM;
        getaddrinfo(timeServer, "123", &hints, &res);
        if (res) {
            freeaddrinfo(res);
        }
        WSACleanup();
    }

    // Sleep briefly so monitoring captures normal activity
    Sleep(1000);

    printf("[*] Legitimate utility process finished successfully.\n");
    return 0;
}
