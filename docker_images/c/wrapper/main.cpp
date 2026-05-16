// Copyright (c) Microsoft. All rights reserved.
// Licensed under the MIT license. See LICENSE file in the project root for full license information.

#include <string>
#include <memory>
#include <cstdlib>
#include <fstream>
#include <cassert>
#include <restbed>
#include <streambuf>
#include <iostream>
#include "ModuleApi.h"
#include "ControlApi.h"
#include "RegistryApi.h"
#include "ServiceApi.h"
#include "DeviceApi.h"
#include "logger.h"
#include "iothub.h"

// logger_init() is required by c-logging-v2 (new SDK) but doesn't exist in older SDKs.
// Use a weak symbol so the binary links regardless of SDK version.
#if unix
extern "C" __attribute__((weak)) int logger_init(void);
#endif

#if unix
#include "unistd.h"
#include <signal.h>
#include <execinfo.h>

static void sigsegv_handler(int sig)
{
    void *frames[64];
    int count = backtrace(frames, 64);
    fprintf(stderr, "\n*** SIGSEGV (signal %d) ***\n", sig);
    backtrace_symbols_fd(frames, count, STDERR_FILENO);
    _exit(139);
}
#endif

using namespace std;
using namespace restbed;
using namespace io::swagger::server::api;

void global_error_handler(const int, const exception& e, const shared_ptr<Session> session)
{
    cerr << "Unhandled exception: " << e.what() << endl;
    if (session && session->is_open())
    {
        string body = string("{\"error\": \"") + e.what() + "\"}";
        session->close(500, body, { {"Content-Type", "application/json"}, {"Connection", "close"} });
    }
}

void launch_system_control_app()
{
#if unix
    pid_t new_pid = fork();
    if (new_pid == 0)
    {
        const char *argv[] = { "/usr/bin/python", "/system_control_app/main.py", NULL}; 
        if (execvp(argv[0], (char**)argv) == -1) 
        {
            std::cout << "execve falied" << std::endl;
            exit(EXIT_FAILURE);
        }
    } 
    else if (new_pid == -1)
    {
        std::cout << "fork failed" << std::endl;
    }
#endif
}

class MergedApi : public ModuleApi, public ControlApi, public RegistryApi, public ServiceApi, public DeviceApi
{
public:
    MergedApi()
    {
        ModuleApi *moduleApi = this;
        ControlApi *controlApi = this;
        RegistryApi *registryApi = this;
        ServiceApi *serviceApi = this;
        DeviceApi *deviceApi = this;
        // Any Api objects derived from restbed::Service need to be derived with a virtual base class as follows:
        //   class  ControlApi: public virtual restbed::Service
        // This allows the MergedApi object to derive from all the Api objects and share a single restbed::Service instance.
        // These asserts verify that all of the Api objects share the same restbed::Service base instance.
        assert((restbed::Service*)moduleApi == (restbed::Service*)controlApi);
        assert((restbed::Service*)moduleApi == (restbed::Service*)registryApi);
        assert((restbed::Service*)moduleApi == (restbed::Service*)serviceApi);
        assert((restbed::Service*)deviceApi == (restbed::Service*)serviceApi);
    }
    using ModuleApi::startService;
    using ModuleApi::stopService;
};

int port = 8082;

int main(const int, const char**)
{
#if unix
    signal(SIGSEGV, sigsegv_handler);
    signal(SIGABRT, sigsegv_handler);
    if (logger_init) {
        logger_init();
    }
#endif

    IoTHub_Init();

    launch_system_control_app();

    auto api = make_shared< MergedApi >();
    cout << "listening on port " << std::to_string(port) << endl;
    api->set_logger( make_shared< CustomLogger >( ) );
    api->set_error_handler( global_error_handler );
    api->startService(port);
    return EXIT_SUCCESS;
}

