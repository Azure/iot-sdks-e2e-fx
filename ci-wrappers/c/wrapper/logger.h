#pragma once

#include <memory>
#include <cstdio>
#include <cstdarg>
#include <cstdlib>
#include <restbed>

using namespace std;
using namespace restbed;

class CustomLogger : public Logger
{
    public:
        void stop( void )
        {
            return;
        }
        
        void start( const shared_ptr< const Settings >& )
        {
            return;
        }

        const char *level_to_name(const Level level)
        {
            switch(level) 
            {
                case INFO: return "INFO";
                case DEBUG: return "DEBUG";
                case FATAL: return "FATAL";
                case ERROR: return "ERROR";
                case WARNING: return "WARNING";
                case SECURITY: return "SECURITY";
                default: return "(unknown level)";
            }
        }
        
        void log( const Level level, const char* format, ... )
        {
            va_list arguments;
            va_start( arguments, format );
           
            fprintf( stdout, "RESTBED:%s: ", level_to_name(level) );
            vfprintf( stdout, format, arguments );
            fprintf( stdout, "\n" );
            
            va_end( arguments );
        }
        
        void log_if( bool expression, const Level level, const char* format, ... )
        {
            if ( expression )
            {
                va_list arguments;
                va_start( arguments, format );
                log( level, format, arguments );
                va_end( arguments );
            }
        }
};

