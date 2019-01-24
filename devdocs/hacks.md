# Hacks used in making this project

1. The restbed code generator has a bug where query parameters with boxcar_naming are put into the code with camelCase, so a query parameter of `connection_string` will generate `request->get_query_parameter("connectionString", "");`.  Until this can be fixed in the generator, this code needs to me manually edited to `request->get_query_parameter("connection_string", "");

1. C++ codegen includes `#include 'Object.h'`.  This header isn't used and causes a compile error.  This line can be removed.

1. C# codegen has `using IO.Swagger.Models`.  This isn't needed.  Remove this if it causes problems.

1. C# codegen doesn't like accepting bodies with type = "text/plain".  It enforces "text/json" and I'm not sure how to override this :(

1. C# codegen doesn't like boxcar_naming.  Just use camelCase everywhere.

1. The flask server we use for python doesn't look like it supports 2.7.  we may only be able to test on 3.6 :(

