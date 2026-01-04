#!/usr/bin/env python3
"""
.NET Development Training Data Generator
Target: ~200 examples for C#, ASP.NET Core, Entity Framework
"""

import json
import random
from pathlib import Path
from typing import List, Dict

SYSTEM_PROMPT = """You are AJ, an expert AI assistant for .NET development.
You help with C#, ASP.NET Core, Entity Framework, and .NET best practices."""

# =============================================================================
# TOOL SELECTION TASKS
# =============================================================================

DOTNET_CLI_TASKS = [
    {
        "instruction": "Create new ASP.NET Core Web API project",
        "command": "dotnet new webapi -n MyApi -f net8.0",
        "explanation": "Creates .NET 8 Web API with default template"
    },
    {
        "instruction": "Create solution and add projects",
        "command": "dotnet new sln -n MySolution && dotnet sln add src/MyApi/MyApi.csproj tests/MyApi.Tests/MyApi.Tests.csproj",
        "explanation": "Creates solution file and adds existing projects"
    },
    {
        "instruction": "Add NuGet package to project",
        "command": "dotnet add package Microsoft.EntityFrameworkCore.SqlServer --version 8.0.0",
        "explanation": "Adds EF Core SQL Server provider"
    },
    {
        "instruction": "Run .NET project in watch mode",
        "command": "dotnet watch run",
        "explanation": "Runs with hot reload for development"
    },
    {
        "instruction": "Run unit tests with coverage",
        "command": "dotnet test --collect:\"XPlat Code Coverage\" --results-directory ./coverage",
        "explanation": "Runs tests and collects coverage data"
    },
    {
        "instruction": "Create EF Core migration",
        "command": "dotnet ef migrations add InitialCreate --project src/MyApi --startup-project src/MyApi",
        "explanation": "Creates database migration from model changes"
    },
    {
        "instruction": "Apply EF Core migrations",
        "command": "dotnet ef database update --project src/MyApi --startup-project src/MyApi",
        "explanation": "Applies pending migrations to database"
    },
    {
        "instruction": "Publish release build",
        "command": "dotnet publish -c Release -o ./publish --self-contained false",
        "explanation": "Framework-dependent publish for deployment"
    },
    {
        "instruction": "Create self-contained single file executable",
        "command": "dotnet publish -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true -o ./publish",
        "explanation": "Single EXE with all dependencies included"
    },
    {
        "instruction": "Format C# code",
        "command": "dotnet format",
        "explanation": "Formats code according to .editorconfig"
    },
    {
        "instruction": "Create new console application",
        "command": "dotnet new console -n MyConsoleApp -f net8.0",
        "explanation": "Creates basic console app with .NET 8"
    },
    {
        "instruction": "Create new class library",
        "command": "dotnet new classlib -n MyLib -f net8.0",
        "explanation": "Creates reusable class library"
    },
    {
        "instruction": "Create xUnit test project",
        "command": "dotnet new xunit -n MyApi.Tests -f net8.0",
        "explanation": "Creates xUnit test project"
    },
    {
        "instruction": "Create Blazor WebAssembly app",
        "command": "dotnet new blazorwasm -n MyBlazorApp -f net8.0",
        "explanation": "Creates client-side Blazor application"
    },
    {
        "instruction": "Create Worker Service",
        "command": "dotnet new worker -n MyWorkerService -f net8.0",
        "explanation": "Creates background service application"
    },
    {
        "instruction": "List available project templates",
        "command": "dotnet new list",
        "explanation": "Shows all installed project templates"
    },
    {
        "instruction": "Build project in Release mode",
        "command": "dotnet build -c Release",
        "explanation": "Compiles project with release optimizations"
    },
    {
        "instruction": "Clean build artifacts",
        "command": "dotnet clean",
        "explanation": "Removes bin and obj directories"
    },
    {
        "instruction": "Restore NuGet packages",
        "command": "dotnet restore",
        "explanation": "Downloads all NuGet dependencies"
    },
    {
        "instruction": "Remove NuGet package",
        "command": "dotnet remove package Microsoft.EntityFrameworkCore",
        "explanation": "Removes package reference from project"
    },
    {
        "instruction": "List NuGet packages",
        "command": "dotnet list package",
        "explanation": "Shows all package references in project"
    },
    {
        "instruction": "Update outdated packages",
        "command": "dotnet list package --outdated",
        "explanation": "Shows packages with newer versions available"
    },
    {
        "instruction": "Add project reference",
        "command": "dotnet add reference ../MyLib/MyLib.csproj",
        "explanation": "Adds reference to another project"
    },
    {
        "instruction": "Run specific test",
        "command": "dotnet test --filter \"FullyQualifiedName~UserServiceTests.CreateUser\"",
        "explanation": "Runs tests matching filter pattern"
    },
    {
        "instruction": "Run tests in specific project",
        "command": "dotnet test tests/MyApi.Tests/MyApi.Tests.csproj",
        "explanation": "Runs tests in specific test project"
    },
    {
        "instruction": "Generate EF Core migration script",
        "command": "dotnet ef migrations script --idempotent -o migration.sql",
        "explanation": "Generates SQL script for migrations"
    },
    {
        "instruction": "Rollback EF Core migration",
        "command": "dotnet ef database update PreviousMigration",
        "explanation": "Reverts database to specific migration"
    },
    {
        "instruction": "Remove last EF Core migration",
        "command": "dotnet ef migrations remove",
        "explanation": "Removes most recent unapplied migration"
    },
    {
        "instruction": "Scaffold DbContext from existing database",
        "command": "dotnet ef dbcontext scaffold \"Server=.;Database=MyDb;Trusted_Connection=True;\" Microsoft.EntityFrameworkCore.SqlServer -o Models",
        "explanation": "Reverse engineers database to C# models"
    },
    {
        "instruction": "Install EF Core tools globally",
        "command": "dotnet tool install --global dotnet-ef",
        "explanation": "Installs EF Core CLI tools"
    },
    {
        "instruction": "Update global tools",
        "command": "dotnet tool update --global dotnet-ef",
        "explanation": "Updates EF Core CLI to latest version"
    },
    {
        "instruction": "Create tool manifest",
        "command": "dotnet new tool-manifest",
        "explanation": "Creates .config/dotnet-tools.json for local tools"
    },
    {
        "instruction": "Run .NET with custom environment",
        "command": "dotnet run --environment Development",
        "explanation": "Runs with specific ASPNETCORE_ENVIRONMENT"
    },
    {
        "instruction": "Generate user secrets ID",
        "command": "dotnet user-secrets init",
        "explanation": "Initializes user secrets for project"
    },
    {
        "instruction": "Set user secret",
        "command": "dotnet user-secrets set \"ConnectionStrings:Default\" \"Server=localhost;Database=MyDb;\"",
        "explanation": "Sets development secret outside code"
    },
    {
        "instruction": "List user secrets",
        "command": "dotnet user-secrets list",
        "explanation": "Shows all configured user secrets"
    },
    {
        "instruction": "Create NuGet package",
        "command": "dotnet pack -c Release -o ./nupkg",
        "explanation": "Creates NuGet package from class library"
    },
    {
        "instruction": "Push NuGet package",
        "command": "dotnet nuget push ./nupkg/MyLib.1.0.0.nupkg --source https://api.nuget.org/v3/index.json --api-key YOUR_API_KEY",
        "explanation": "Publishes package to NuGet.org"
    },
    {
        "instruction": "Add NuGet source",
        "command": "dotnet nuget add source https://pkgs.dev.azure.com/myorg/_packaging/myfeed/nuget/v3/index.json -n MyFeed",
        "explanation": "Adds private NuGet feed"
    },
    {
        "instruction": "Check .NET SDK version",
        "command": "dotnet --version",
        "explanation": "Shows installed SDK version"
    },
    {
        "instruction": "List installed SDKs",
        "command": "dotnet --list-sdks",
        "explanation": "Shows all installed .NET SDK versions"
    },
    {
        "instruction": "List installed runtimes",
        "command": "dotnet --list-runtimes",
        "explanation": "Shows all installed .NET runtime versions"
    },
    {
        "instruction": "Create global.json for SDK version",
        "command": "dotnet new globaljson --sdk-version 8.0.100",
        "explanation": "Pins project to specific SDK version"
    },
    {
        "instruction": "Run with HTTPS development certificate",
        "command": "dotnet dev-certs https --trust",
        "explanation": "Trusts development HTTPS certificate"
    },
    {
        "instruction": "Analyze code with dotnet format",
        "command": "dotnet format --verify-no-changes",
        "explanation": "Checks formatting without making changes"
    },
    {
        "instruction": "Publish for Linux",
        "command": "dotnet publish -c Release -r linux-x64 --self-contained true",
        "explanation": "Cross-compiles for Linux x64"
    },
    {
        "instruction": "Publish trimmed application",
        "command": "dotnet publish -c Release -r win-x64 -p:PublishTrimmed=true",
        "explanation": "Removes unused code for smaller output"
    },
    {
        "instruction": "Create AOT compiled application",
        "command": "dotnet publish -c Release -r win-x64 -p:PublishAot=true",
        "explanation": "Native AOT compilation (requires specific setup)"
    },
]

# =============================================================================
# CODE EXAMPLES
# =============================================================================

CODE_EXAMPLES = [
    {
        "instruction": "Create ASP.NET Core minimal API with dependency injection",
        "language": "csharp",
        "code": """using Microsoft.EntityFrameworkCore;

var builder = WebApplication.CreateBuilder(args);

// Configure services
builder.Services.AddDbContext<AppDbContext>(options =>
    options.UseSqlServer(builder.Configuration.GetConnectionString("Default")));
builder.Services.AddScoped<IUserService, UserService>();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

var app = builder.Build();

// Configure middleware
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseHttpsRedirection();

// Map endpoints
app.MapGet("/users", async (IUserService userService) =>
    await userService.GetAllAsync())
    .WithName("GetUsers")
    .WithOpenApi();

app.MapGet("/users/{id:int}", async (int id, IUserService userService) =>
    await userService.GetByIdAsync(id) is User user
        ? Results.Ok(user)
        : Results.NotFound())
    .WithName("GetUser")
    .WithOpenApi();

app.MapPost("/users", async (CreateUserDto dto, IUserService userService) =>
{
    var user = await userService.CreateAsync(dto);
    return Results.Created($"/users/{user.Id}", user);
})
    .WithName("CreateUser")
    .WithOpenApi();

app.Run();

// DTOs and interfaces
public record CreateUserDto(string Name, string Email);
public record User(int Id, string Name, string Email, DateTime CreatedAt);

public interface IUserService
{
    Task<IEnumerable<User>> GetAllAsync();
    Task<User?> GetByIdAsync(int id);
    Task<User> CreateAsync(CreateUserDto dto);
}""",
        "explanation": "Minimal API with DI, EF Core, Swagger, and proper patterns"
    },
    {
        "instruction": "Implement repository pattern with Entity Framework Core",
        "language": "csharp",
        "code": """using Microsoft.EntityFrameworkCore;
using System.Linq.Expressions;

// Generic repository interface
public interface IRepository<T> where T : class
{
    Task<T?> GetByIdAsync(int id);
    Task<IEnumerable<T>> GetAllAsync();
    Task<IEnumerable<T>> FindAsync(Expression<Func<T, bool>> predicate);
    Task<T> AddAsync(T entity);
    Task UpdateAsync(T entity);
    Task DeleteAsync(T entity);
    Task<bool> ExistsAsync(int id);
}

// Generic repository implementation
public class Repository<T> : IRepository<T> where T : class
{
    protected readonly AppDbContext _context;
    protected readonly DbSet<T> _dbSet;

    public Repository(AppDbContext context)
    {
        _context = context;
        _dbSet = context.Set<T>();
    }

    public virtual async Task<T?> GetByIdAsync(int id)
        => await _dbSet.FindAsync(id);

    public virtual async Task<IEnumerable<T>> GetAllAsync()
        => await _dbSet.ToListAsync();

    public virtual async Task<IEnumerable<T>> FindAsync(Expression<Func<T, bool>> predicate)
        => await _dbSet.Where(predicate).ToListAsync();

    public virtual async Task<T> AddAsync(T entity)
    {
        await _dbSet.AddAsync(entity);
        await _context.SaveChangesAsync();
        return entity;
    }

    public virtual async Task UpdateAsync(T entity)
    {
        _dbSet.Update(entity);
        await _context.SaveChangesAsync();
    }

    public virtual async Task DeleteAsync(T entity)
    {
        _dbSet.Remove(entity);
        await _context.SaveChangesAsync();
    }

    public virtual async Task<bool> ExistsAsync(int id)
        => await _dbSet.FindAsync(id) != null;
}

// Specialized repository with includes
public class UserRepository : Repository<User>, IUserRepository
{
    public UserRepository(AppDbContext context) : base(context) { }

    public async Task<User?> GetWithOrdersAsync(int id)
        => await _dbSet
            .Include(u => u.Orders)
            .FirstOrDefaultAsync(u => u.Id == id);
}""",
        "explanation": "Generic and specialized repository pattern with EF Core"
    },
    {
        "instruction": "Create middleware for request logging and error handling",
        "language": "csharp",
        "code": """using System.Diagnostics;
using System.Text.Json;

// Request logging middleware
public class RequestLoggingMiddleware
{
    private readonly RequestDelegate _next;
    private readonly ILogger<RequestLoggingMiddleware> _logger;

    public RequestLoggingMiddleware(RequestDelegate next, ILogger<RequestLoggingMiddleware> logger)
    {
        _next = next;
        _logger = logger;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        var requestId = Guid.NewGuid().ToString("N")[..8];
        var stopwatch = Stopwatch.StartNew();
        
        context.Items["RequestId"] = requestId;
        context.Response.Headers.Append("X-Request-Id", requestId);

        _logger.LogInformation(
            "Request {RequestId} {Method} {Path} started",
            requestId, context.Request.Method, context.Request.Path);

        await _next(context);

        stopwatch.Stop();
        _logger.LogInformation(
            "Request {RequestId} completed in {Duration}ms with status {StatusCode}",
            requestId, stopwatch.ElapsedMilliseconds, context.Response.StatusCode);
    }
}

// Global error handling middleware
public class ErrorHandlingMiddleware
{
    private readonly RequestDelegate _next;
    private readonly ILogger<ErrorHandlingMiddleware> _logger;
    private readonly IHostEnvironment _env;

    public ErrorHandlingMiddleware(RequestDelegate next, ILogger<ErrorHandlingMiddleware> logger, IHostEnvironment env)
    {
        _next = next;
        _logger = logger;
        _env = env;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        try
        {
            await _next(context);
        }
        catch (Exception ex)
        {
            var requestId = context.Items["RequestId"]?.ToString() ?? "unknown";
            _logger.LogError(ex, "Request {RequestId} failed with exception", requestId);
            
            await HandleExceptionAsync(context, ex, requestId);
        }
    }

    private async Task HandleExceptionAsync(HttpContext context, Exception exception, string requestId)
    {
        context.Response.ContentType = "application/json";
        
        var (statusCode, message) = exception switch
        {
            ArgumentException => (400, exception.Message),
            KeyNotFoundException => (404, "Resource not found"),
            UnauthorizedAccessException => (401, "Unauthorized"),
            _ => (500, "An error occurred processing your request")
        };

        context.Response.StatusCode = statusCode;

        var response = new
        {
            error = message,
            requestId,
            details = _env.IsDevelopment() ? exception.ToString() : null
        };

        await context.Response.WriteAsJsonAsync(response);
    }
}

// Extension methods for registration
public static class MiddlewareExtensions
{
    public static IApplicationBuilder UseRequestLogging(this IApplicationBuilder builder)
        => builder.UseMiddleware<RequestLoggingMiddleware>();

    public static IApplicationBuilder UseErrorHandling(this IApplicationBuilder builder)
        => builder.UseMiddleware<ErrorHandlingMiddleware>();
}""",
        "explanation": "Custom middleware for logging and exception handling"
    },
    {
        "instruction": "Implement async/await best practices with proper cancellation",
        "language": "csharp",
        "code": """public class DataProcessor
{
    private readonly HttpClient _httpClient;
    private readonly ILogger<DataProcessor> _logger;

    public DataProcessor(HttpClient httpClient, ILogger<DataProcessor> logger)
    {
        _httpClient = httpClient;
        _logger = logger;
    }

    // Always accept CancellationToken for async operations
    public async Task<Result<Data>> ProcessAsync(
        string url, 
        CancellationToken cancellationToken = default)
    {
        try
        {
            // Pass cancellation token to async calls
            var response = await _httpClient.GetAsync(url, cancellationToken);
            response.EnsureSuccessStatusCode();
            
            var content = await response.Content.ReadAsStringAsync(cancellationToken);
            var data = JsonSerializer.Deserialize<Data>(content);
            
            return Result<Data>.Success(data!);
        }
        catch (OperationCanceledException)
        {
            _logger.LogInformation("Operation was cancelled");
            return Result<Data>.Failure("Operation cancelled");
        }
        catch (HttpRequestException ex)
        {
            _logger.LogError(ex, "HTTP request failed");
            return Result<Data>.Failure($"HTTP error: {ex.Message}");
        }
    }

    // Parallel processing with semaphore for throttling
    public async Task<IEnumerable<Result<Data>>> ProcessManyAsync(
        IEnumerable<string> urls,
        int maxConcurrency = 5,
        CancellationToken cancellationToken = default)
    {
        var semaphore = new SemaphoreSlim(maxConcurrency);
        
        var tasks = urls.Select(async url =>
        {
            await semaphore.WaitAsync(cancellationToken);
            try
            {
                return await ProcessAsync(url, cancellationToken);
            }
            finally
            {
                semaphore.Release();
            }
        });

        return await Task.WhenAll(tasks);
    }

    // ConfigureAwait(false) for library code
    public async Task<string> LibraryMethodAsync(CancellationToken ct = default)
    {
        // Use ConfigureAwait(false) in library code to avoid deadlocks
        var result = await SomeAsyncOperation().ConfigureAwait(false);
        return result;
    }
}

// Result pattern for explicit success/failure
public record Result<T>
{
    public bool IsSuccess { get; init; }
    public T? Value { get; init; }
    public string? Error { get; init; }

    public static Result<T> Success(T value) => new() { IsSuccess = true, Value = value };
    public static Result<T> Failure(string error) => new() { IsSuccess = false, Error = error };
}""",
        "explanation": "Async best practices: cancellation, parallel with throttling, Result pattern"
    },
    {
        "instruction": "Configure dependency injection with options pattern",
        "language": "csharp",
        "code": """// Configuration classes
public class EmailSettings
{
    public const string SectionName = "Email";
    
    public required string SmtpServer { get; init; }
    public int Port { get; init; } = 587;
    public required string FromAddress { get; init; }
    public string? Username { get; init; }
    public string? Password { get; init; }
    public bool UseSsl { get; init; } = true;
}

public class ApiSettings
{
    public const string SectionName = "Api";
    
    public required string BaseUrl { get; init; }
    public int TimeoutSeconds { get; init; } = 30;
    public int RetryCount { get; init; } = 3;
}

// Service registration extension
public static class ServiceCollectionExtensions
{
    public static IServiceCollection AddApplicationServices(
        this IServiceCollection services,
        IConfiguration configuration)
    {
        // Options pattern - binds to configuration section
        services.Configure<EmailSettings>(
            configuration.GetSection(EmailSettings.SectionName));
        services.Configure<ApiSettings>(
            configuration.GetSection(ApiSettings.SectionName));

        // Validate options at startup
        services.AddOptions<EmailSettings>()
            .Bind(configuration.GetSection(EmailSettings.SectionName))
            .ValidateDataAnnotations()
            .ValidateOnStart();

        // Register services with different lifetimes
        services.AddSingleton<ICacheService, RedisCacheService>();  // One instance
        services.AddScoped<IUserService, UserService>();            // Per request
        services.AddTransient<IEmailService, EmailService>();       // New each time

        // Typed HttpClient
        services.AddHttpClient<IExternalApiClient, ExternalApiClient>((sp, client) =>
        {
            var settings = sp.GetRequiredService<IOptions<ApiSettings>>().Value;
            client.BaseAddress = new Uri(settings.BaseUrl);
            client.Timeout = TimeSpan.FromSeconds(settings.TimeoutSeconds);
        })
        .AddPolicyHandler(GetRetryPolicy());

        return services;
    }

    private static IAsyncPolicy<HttpResponseMessage> GetRetryPolicy()
    {
        return HttpPolicyExtensions
            .HandleTransientHttpError()
            .WaitAndRetryAsync(3, retryAttempt =>
                TimeSpan.FromSeconds(Math.Pow(2, retryAttempt)));
    }
}

// Using options in service
public class EmailService : IEmailService
{
    private readonly EmailSettings _settings;
    private readonly ILogger<EmailService> _logger;

    public EmailService(
        IOptions<EmailSettings> options,  // IOptions<T> for singleton-safe config
        ILogger<EmailService> logger)
    {
        _settings = options.Value;
        _logger = logger;
    }

    // For config that can change at runtime, use IOptionsMonitor<T>
}""",
        "explanation": "Options pattern, service lifetimes, typed HttpClient with Polly"
    },
]

# =============================================================================
# MULTI-STEP PLANNING TASKS
# =============================================================================

PLANNING_TASKS = [
    {
        "instruction": "Create new ASP.NET Core Web API project with clean architecture",
        "steps": [
            "Create solution: dotnet new sln -n MyApp",
            "Create projects: Api, Application, Domain, Infrastructure",
            "Domain: entities, value objects, interfaces, no dependencies",
            "Application: use cases, DTOs, validators (references Domain)",
            "Infrastructure: EF Core, external services (references Application)",
            "Api: controllers, middleware, config (references Application, Infrastructure)",
            "Add project references following dependency rule",
            "Set up dependency injection in Program.cs",
            "Add global error handling middleware",
            "Configure Serilog for structured logging",
            "Add health checks endpoint",
            "Configure Swagger with XML comments",
            "Add FluentValidation for request validation",
            "Set up MediatR for CQRS pattern",
            "Create Dockerfile for containerization"
        ]
    },
    {
        "instruction": "Implement authentication with JWT and refresh tokens",
        "steps": [
            "Add Microsoft.AspNetCore.Authentication.JwtBearer package",
            "Create TokenSettings configuration class",
            "Implement ITokenService for generating tokens",
            "Create access token with short expiry (15 min)",
            "Create refresh token with longer expiry (7 days)",
            "Store refresh tokens in database with user association",
            "Implement login endpoint returning both tokens",
            "Implement refresh endpoint validating refresh token",
            "Add JWT authentication in Program.cs",
            "Create AuthorizeAttribute for role-based access",
            "Implement revocation for logout",
            "Add rate limiting on auth endpoints",
            "Test with integration tests"
        ]
    },
    {
        "instruction": "Set up Entity Framework Core with migrations and seeding",
        "steps": [
            "Add EF Core packages (SqlServer, Design, Tools)",
            "Create DbContext inheriting from DbContext",
            "Define entity classes with proper annotations",
            "Configure relationships in OnModelCreating",
            "Create IEntityTypeConfiguration classes for complex configs",
            "Add connection string to appsettings.json",
            "Register DbContext in DI with connection string",
            "Create initial migration: dotnet ef migrations add Initial",
            "Create seed data in OnModelCreating or separate class",
            "Apply migrations: dotnet ef database update",
            "Add database health check",
            "Set up migration in CI/CD pipeline",
            "Add indexes for frequently queried columns"
        ]
    },
]

# =============================================================================
# CONCEPT Q&A
# =============================================================================

BASIC_CONCEPTS = [
    {
        "question": "What is dependency injection in .NET?",
        "answer": "DI is built into ASP.NET Core. Register services in Program.cs, framework injects into constructors. Three lifetimes: Singleton (one instance), Scoped (per HTTP request), Transient (new each injection). Use interfaces for abstraction. Register with AddSingleton/AddScoped/AddTransient. Benefits: testability (mock dependencies), loose coupling, configuration flexibility. Common mistake: injecting scoped into singleton (captive dependency). Use IServiceProvider for factory patterns."
    },
    {
        "question": "What is Entity Framework Core?",
        "answer": "EF Core is Microsoft's ORM for .NET. Maps C# classes to database tables. DbContext is unit of work. DbSet<T> for queries and changes. LINQ translates to SQL. Features: migrations (schema versioning), change tracking, lazy/eager loading. Common patterns: repository, unit of work. Pros: productivity, type safety, database agnostic. Cons: can generate inefficient queries, learning curve for complex scenarios. Use AsNoTracking() for read-only queries. Consider Dapper for performance-critical paths."
    },
    {
        "question": "How do I handle configuration in ASP.NET Core?",
        "answer": "Built-in configuration system supports multiple sources: appsettings.json, environment variables, user secrets, Azure Key Vault. Access via IConfiguration or Options pattern (recommended). Options pattern: define settings class, bind in Program.cs with Configure<T>, inject IOptions<T>. Hierarchy: appsettings.json < appsettings.{Environment}.json < env vars < command line. Use user secrets for local dev secrets (dotnet user-secrets). Never commit secrets to git."
    },
    {
        "question": "What are the differences between .NET versions?",
        "answer": ".NET Framework: Windows-only, legacy, 4.8 is final. .NET Core: cross-platform, modern, versions 2-3. .NET 5+: unified platform, replaces both. Current: .NET 8 (LTS), .NET 9 (latest). LTS = 3 years support. Key features by version: .NET 6 (minimal APIs, global usings), .NET 7 (performance), .NET 8 (AOT, improved containers). Always target latest LTS for new projects. Migration path available from Framework to modern .NET."
    },
    {
        "question": "What is async/await in C#?",
        "answer": "Async/await enables non-blocking I/O operations. Mark method with async, return Task or Task<T>. await pauses method until Task completes without blocking thread. Use for: database calls, HTTP requests, file I/O. Don't use for CPU-bound work (use Task.Run). Async all the way: don't mix sync and async. Avoid async void except for event handlers. ConfigureAwait(false) in libraries to avoid deadlocks. ValueTask for hot paths that often complete synchronously."
    },
    {
        "question": "What is middleware in ASP.NET Core?",
        "answer": "Middleware are components in request pipeline. Each can process request, call next, process response. Order matters - first added executes first. Built-in: authentication, authorization, static files, CORS, routing. Custom middleware: RequestDelegate in constructor, Invoke/InvokeAsync method. Use app.Use() for inline, app.UseMiddleware<T>() for classes. Terminal middleware: doesn't call next (like endpoints). Common: logging, error handling, request timing."
    },
    {
        "question": "What is LINQ?",
        "answer": "LINQ (Language Integrated Query) provides query syntax for collections. Two syntaxes: query (from x in collection where ... select ...) and method (collection.Where().Select()). Works with: IEnumerable<T> (in-memory), IQueryable<T> (translates to SQL). Common methods: Where, Select, OrderBy, GroupBy, Join, First/Single/FirstOrDefault, Any, All, Count, Sum. Deferred execution: query doesn't run until enumerated. Force execution with ToList(), ToArray(). EF Core translates to SQL."
    },
    {
        "question": "What are records in C#?",
        "answer": "Records are reference types (or struct with 'record struct') with value semantics. Introduced C# 9. Features: immutability by default, value-based equality, with-expressions for non-destructive mutation, concise syntax. Declaration: record Person(string Name, int Age). Generates: constructor, properties, Equals, GetHashCode, ToString, Deconstruct. Use for: DTOs, value objects, immutable data. Records can inherit from other records. Primary constructors in C# 12 bring similar to classes."
    },
    {
        "question": "What is the difference between interface and abstract class?",
        "answer": "Interface: contract only, multiple inheritance allowed, default implementations since C# 8, no state. Abstract class: can have implementation, state (fields), single inheritance only. When to use: interface for 'can-do' (IDisposable, IComparable), abstract for 'is-a' with shared code. Consider: interfaces for dependency injection, abstract for template method pattern. C# 8 default interface methods blurred distinction. Prefer interfaces for flexibility, abstract class for code reuse with inheritance."
    },
    {
        "question": "How does routing work in ASP.NET Core?",
        "answer": "Two types: conventional (MVC pattern-based) and attribute routing (explicit). Conventional: app.MapControllerRoute() with pattern like {controller}/{action}/{id?}. Attribute: [Route('api/[controller]')], [HttpGet('{id}')]. Route parameters: {id}, {id:int} (constraint), {id?} (optional), {*slug} (catch-all). Route values accessible via RouteData. Minimal APIs: app.MapGet('/path', handler). Endpoint routing separates routing from dispatching. URL generation: LinkGenerator, Url.Action()."
    },
    {
        "question": "What is Razor Pages?",
        "answer": "Razor Pages: page-based model for ASP.NET Core, alternative to MVC. Each page is .cshtml + .cshtml.cs (PageModel). Good for: page-focused scenarios, simpler than full MVC. PageModel contains handlers: OnGet, OnPost, OnGetAsync. Uses Razor syntax like MVC views. Routing based on folder structure (/Pages/Products/Index.cshtml → /Products). Supports: model binding, validation, DI. Choose over MVC for: simpler apps, rapid development. MVC better for: APIs, complex UI logic, reusable controllers."
    },
    {
        "question": "What is Blazor?",
        "answer": "Blazor: build interactive web UI with C# instead of JavaScript. Two hosting models: Blazor Server (runs on server, SignalR for UI updates), Blazor WebAssembly (runs in browser). Components: .razor files with C# + HTML. Share code between client/server. Benefits: full .NET ecosystem, type safety, component model. Considerations: Server requires constant connection; WASM has larger download, startup time. Use for: .NET teams, shared logic, component libraries. Integration with JS still possible."
    },
]

ADVANCED_CONCEPTS = [
    {
        "question": "What is the difference between Task and ValueTask?",
        "answer": "Task allocates heap object every call. ValueTask is struct - no allocation if result available synchronously. Use ValueTask when: method often completes synchronously, called frequently (hot path). Rules: await only once, don't block on ValueTask, cache result if needed multiple times. IValueTaskSource for advanced pooling. Default to Task for most code. Only optimize with ValueTask after profiling shows allocation pressure."
    },
    {
        "question": "How do I implement CQRS with MediatR?",
        "answer": "CQRS separates reads (queries) from writes (commands). MediatR provides mediator pattern implementation. Commands: IRequest<T> for writes, return result/void. Queries: IRequest<T> for reads. Handlers: IRequestHandler<TRequest, TResponse>. Benefits: separation of concerns, easy testing, pipeline behaviors (validation, logging, caching). Register with AddMediatR(). Use behaviors for cross-cutting concerns. Not always needed - adds complexity. Good for: complex domains, event sourcing prep."
    },
    {
        "question": "What are Source Generators in C#?",
        "answer": "Source generators run at compile time, produce C# code added to compilation. Use cases: reduce reflection (JSON serialization), auto-implement patterns, compile-time validation. Examples: System.Text.Json generator, RegexGenerator. Benefits: faster startup (no runtime reflection), AOT compatible, catch errors at compile time. Write generators implementing ISourceGenerator or IIncrementalGenerator. Analyzers complement generators for warnings/errors. Replaces T4 templates for many scenarios."
    },
    {
        "question": "How do I optimize Entity Framework Core queries?",
        "answer": "Common issues: N+1 queries, over-fetching, tracking overhead. Solutions: Use Include() for eager loading, Select() projections for only needed columns, AsNoTracking() for read-only. Split queries for large includes: AsSplitQuery(). Check generated SQL with ToQueryString() or logging. Use raw SQL or Dapper for complex queries. Indexes: add for WHERE/ORDER BY columns. Compiled queries for frequently executed. Batch operations with ExecuteUpdate/ExecuteDelete in EF7+. Profile with MiniProfiler or Application Insights."
    },
    {
        "question": "What is the Channel<T> class?",
        "answer": "Channel<T> is thread-safe producer-consumer pattern implementation. Better than BlockingCollection for async scenarios. Create bounded (capacity limit) or unbounded. Methods: Writer.WriteAsync(), Reader.ReadAsync(), ReadAllAsync(). Use for: async pipelines, rate limiting, background processing. Backpressure: bounded channels make writers wait when full. BoundedChannelOptions configure behavior when full. Useful for: high-throughput scenarios, decoupling producers/consumers. Part of System.Threading.Channels."
    },
    {
        "question": "How do I implement background services?",
        "answer": "IHostedService: interface for background tasks in ASP.NET Core. BackgroundService: base class with ExecuteAsync(). Register with AddHostedService<T>(). Runs alongside web host. Use cases: queue processing, scheduled tasks, long-running operations. Graceful shutdown via CancellationToken. For scheduled tasks: Timer or Quartz.NET/Hangfire for complex scheduling. Consider: IServiceScopeFactory for scoped services, error handling (service stops on exception). Worker Service template for non-web background apps."
    },
    {
        "question": "What is Polly and how do I use it?",
        "answer": "Polly is resilience library for .NET. Policies: Retry (retry failed operations), Circuit Breaker (fail fast when system is down), Timeout, Bulkhead (limit concurrent calls), Fallback, Cache. Chain policies with PolicyWrap. Integrate with HttpClientFactory: AddPolicyHandler(). Use for: external API calls, database connections, any unreliable operation. Example: Policy.Handle<HttpRequestException>().WaitAndRetryAsync(3, i => TimeSpan.FromSeconds(i * 2)). Essential for microservices. Configure based on downstream service characteristics."
    },
    {
        "question": "How do I implement health checks?",
        "answer": "Health checks verify application can handle requests. Built-in: AddHealthChecks(), MapHealthChecks('/health'). Custom: implement IHealthCheck with CheckHealthAsync. Pre-built: EF Core, SQL Server, Redis, RabbitMQ via AspNetCore.Diagnostics.HealthChecks. Response: Healthy, Degraded, Unhealthy. Use for: load balancer probes, Kubernetes readiness/liveness, monitoring. Separate endpoints: /health/ready (can serve traffic), /health/live (process running). Don't make health checks too expensive."
    },
    {
        "question": "What is .NET Native AOT?",
        "answer": "AOT (Ahead-of-Time) compilation produces native executables. No JIT at runtime, no .NET runtime required. Benefits: instant startup, smaller memory, smaller deployment size. Limitations: no dynamic code generation (reflection limitations), no dynamic assembly loading. Works well for: console apps, microservices, serverless. Enable: <PublishAot>true</PublishAot>. Source generators help avoid reflection. Trimming removes unused code. .NET 8 improved compatibility. Test thoroughly - some libraries incompatible."
    },
    {
        "question": "What is minimal API in ASP.NET Core?",
        "answer": "Minimal APIs: lightweight HTTP APIs without controllers. Introduced .NET 6. Define endpoints directly: app.MapGet('/todos', () => db.Todos). Support: route parameters, model binding, DI, filters, authentication. Benefits: less boilerplate, faster startup, good for microservices. Features: route groups, endpoint filters, typed results. Use TypedResults for OpenAPI support. For complex APIs, controllers still valuable. Can mix minimal and controller-based. Good for: small services, serverless, learning."
    },
    {
        "question": "How do I implement API versioning?",
        "answer": "Microsoft.AspNetCore.Mvc.Versioning package (now Asp.Versioning). Strategies: URL segment (/v1/), query string (?api-version=1), header, media type. Configure: AddApiVersioning(), specify default version, report versions. Attribute: [ApiVersion('1.0')], [MapToApiVersion('2.0')]. Deprecation: [ApiVersion('1.0', Deprecated = true)]. Multiple versions per controller/action possible. Combine with OpenAPI: different docs per version. Plan versioning strategy before first release."
    },
    {
        "question": "What is gRPC in .NET?",
        "answer": "gRPC: high-performance RPC framework using Protocol Buffers. Define service in .proto file, generates C# client/server code. Benefits: binary protocol (smaller, faster), streaming, strong typing, code generation. Use cases: microservice communication, high-throughput APIs. Setup: AddGrpc(), MapGrpcService<T>(). Client: GrpcChannel.ForAddress(), create typed client. Limitations: not browser-friendly (needs grpc-web), debugging harder than JSON. Consider for: internal services where performance matters."
    },
]

# =============================================================================
# ERROR SCENARIOS
# =============================================================================

ERROR_SCENARIOS = [
    {
        "instruction": "DbContext disposed error when accessing navigation property",
        "error_type": "ef_core_error",
        "response": {
            "status": "common_issue",
            "cause": "Lazy loading after DbContext disposed, or returning entity outside using block",
            "solutions": [
                "Use eager loading: Include() in query",
                "Project to DTO before returning",
                "Use explicit loading: Entry().Collection().Load()",
                "Ensure DbContext lifetime matches usage (scoped in web apps)"
            ],
            "best_practice": "Always project to DTOs, avoid exposing entities"
        }
    },
    {
        "instruction": "Circular reference in JSON serialization",
        "error_type": "serialization_error",
        "response": {
            "status": "fixable",
            "cause": "Navigation properties create cycles (User -> Orders -> User)",
            "solutions": [
                "Use DTOs without circular references",
                "Configure JSON to ignore cycles: ReferenceHandler.IgnoreCycles",
                "[JsonIgnore] on navigation properties",
                "Use projection in queries: Select(x => new { ... })"
            ],
            "code_fix": "builder.Services.Configure<JsonOptions>(o => o.SerializerOptions.ReferenceHandler = ReferenceHandler.IgnoreCycles);"
        }
    },
    {
        "instruction": "Cannot resolve scoped service from singleton",
        "error_type": "di_error",
        "response": {
            "status": "design_issue",
            "cause": "Singleton holds reference to scoped service (captive dependency)",
            "risk": "Scoped service outlives its intended lifetime, potential concurrency issues",
            "solutions": [
                "Inject IServiceScopeFactory into singleton, create scope when needed",
                "Change singleton to scoped if appropriate",
                "Re-evaluate if singleton is necessary"
            ],
            "code_example": "var scope = _scopeFactory.CreateScope(); var service = scope.ServiceProvider.GetRequiredService<IScopedService>();"
        }
    },
    {
        "instruction": "NullReferenceException in async method",
        "error_type": "null_handling",
        "response": {
            "status": "common_issue",
            "causes": [
                "Awaited task returned null",
                "Null check skipped after await",
                "Navigation property not included in query"
            ],
            "solutions": [
                "Enable nullable reference types (NRTs)",
                "Check for null after awaiting",
                "Use FirstOrDefaultAsync() then check != null",
                "Use null-conditional operators: result?.Property"
            ],
            "prevention": "Enable <Nullable>enable</Nullable> in project file"
        }
    },
    {
        "instruction": "Task was canceled exception",
        "error_type": "cancellation",
        "response": {
            "status": "handle_gracefully",
            "causes": [
                "Client disconnected during request",
                "Request timeout exceeded",
                "CancellationToken explicitly canceled"
            ],
            "handling": [
                "Catch OperationCanceledException",
                "Return appropriate response (client canceled = no response needed)",
                "Log for monitoring, not as error"
            ],
            "code_example": "catch (OperationCanceledException) when (cancellationToken.IsCancellationRequested) { // Request was canceled, cleanup and return }"
        }
    },
    {
        "instruction": "EF Core migration failing",
        "error_type": "migration_error",
        "response": {
            "status": "troubleshoot",
            "common_causes": [
                "Pending model changes not in migration",
                "Data incompatible with new schema",
                "Missing migration files",
                "Connection string issues"
            ],
            "solutions": [
                "Generate new migration: dotnet ef migrations add <name>",
                "Review generated migration for data issues",
                "Add data migration for incompatible changes",
                "Use --verbose flag for detailed errors"
            ],
            "commands": [
                "dotnet ef migrations list",
                "dotnet ef database update --verbose",
                "dotnet ef migrations remove (for last migration)"
            ]
        }
    },
    {
        "instruction": "HTTP 415 Unsupported Media Type",
        "error_type": "content_negotiation",
        "response": {
            "status": "configuration",
            "cause": "Request Content-Type not supported by endpoint",
            "solutions": [
                "Ensure client sends Content-Type: application/json",
                "Add [Consumes('application/json')] attribute",
                "Configure JSON input formatters in services",
                "Check model binding configuration"
            ],
            "common_mistake": "Missing Content-Type header in POST/PUT requests"
        }
    },
    {
        "instruction": "Deadlock in async code",
        "error_type": "threading",
        "response": {
            "status": "critical",
            "cause": "Blocking on async code in synchronization context (e.g., .Result or .Wait())",
            "solutions": [
                "Use async all the way - never .Result or .Wait()",
                "Use ConfigureAwait(false) in library code",
                "If must block: use .GetAwaiter().GetResult() with caution",
                "Consider synchronous alternatives if available"
            ],
            "prevention": "Never mix sync and async, especially in ASP.NET Core"
        }
    },
    {
        "instruction": "Memory leak in ASP.NET Core application",
        "error_type": "performance",
        "response": {
            "status": "investigate",
            "common_causes": [
                "Static event handlers not unsubscribed",
                "Captive dependencies (scoped in singleton)",
                "Large objects in cache without eviction",
                "IDisposable not disposed"
            ],
            "debugging_tools": [
                "dotnet-counters for runtime metrics",
                "dotnet-dump for memory snapshots",
                "Visual Studio diagnostic tools",
                "Application Insights memory profiling"
            ],
            "solutions": [
                "Review singleton lifetimes",
                "Implement IDisposable properly",
                "Use weak references for caches",
                "Profile with memory profiler"
            ]
        }
    },
    {
        "instruction": "SignalR connection dropping",
        "error_type": "real_time",
        "response": {
            "status": "troubleshoot",
            "causes": [
                "Network timeout or instability",
                "Load balancer not configured for WebSocket",
                "Azure SignalR Service limits exceeded",
                "Client not handling reconnection"
            ],
            "solutions": [
                "Enable automatic reconnection on client",
                "Configure sticky sessions if load balanced",
                "Use Azure SignalR Service for scale",
                "Implement OnReconnected handler"
            ],
            "client_code": "connection.onreconnecting(error => console.log('Reconnecting...'))"
        }
    },
    {
        "instruction": "Antiforgery token validation failed",
        "error_type": "security",
        "response": {
            "status": "configuration",
            "cause": "CSRF token mismatch between form and server",
            "common_causes": [
                "Missing @Html.AntiForgeryToken() in form",
                "Token expired",
                "Multiple instances with different keys",
                "SPA not including token in AJAX requests"
            ],
            "solutions": [
                "Add [ValidateAntiForgeryToken] attribute",
                "Configure data protection keys for multi-instance",
                "For APIs: use token header with JavaScript",
                "Exclude specific endpoints with [IgnoreAntiforgeryToken]"
            ]
        }
    },
    {
        "instruction": "SSL/TLS connection error to database",
        "error_type": "connectivity",
        "response": {
            "status": "configuration",
            "causes": [
                "SSL certificate not trusted",
                "TLS version mismatch",
                "Certificate expired",
                "Connection string missing encryption settings"
            ],
            "solutions": [
                "For dev: TrustServerCertificate=true (don't use in prod)",
                "Install/trust certificate on server",
                "Verify connection string encryption settings",
                "Check SQL Server TLS configuration"
            ],
            "connection_string": "Server=...;Encrypt=true;TrustServerCertificate=false;"
        }
    },
]

# =============================================================================
# GENERATOR FUNCTIONS
# =============================================================================

def format_command_response(command: str, explanation: str) -> str:
    return json.dumps({
        "action": "execute_command",
        "command": command,
        "explanation": explanation
    }, indent=2)

def format_code_response(language: str, code: str, explanation: str) -> str:
    return json.dumps({
        "action": "provide_code",
        "language": language,
        "code": code,
        "explanation": explanation
    }, indent=2)

def format_planning_response(steps: List[str]) -> str:
    return json.dumps({
        "action": "multi_step_plan",
        "steps": [{"step": i+1, "action": step} for i, step in enumerate(steps)],
    }, indent=2)

def format_error_response(error_data: dict) -> str:
    return json.dumps(error_data, indent=2)

def generate_tool_examples() -> List[Dict]:
    return [{
        "system": SYSTEM_PROMPT,
        "instruction": task["instruction"],
        "response": format_command_response(task["command"], task["explanation"])
    } for task in DOTNET_CLI_TASKS]

def generate_code_examples() -> List[Dict]:
    return [{
        "system": SYSTEM_PROMPT,
        "instruction": ex["instruction"],
        "response": format_code_response(ex["language"], ex["code"], ex["explanation"])
    } for ex in CODE_EXAMPLES]

def generate_planning_examples() -> List[Dict]:
    return [{
        "system": SYSTEM_PROMPT,
        "instruction": task["instruction"],
        "response": format_planning_response(task["steps"])
    } for task in PLANNING_TASKS]

def generate_concept_examples() -> List[Dict]:
    all_concepts = BASIC_CONCEPTS + ADVANCED_CONCEPTS
    return [{
        "system": SYSTEM_PROMPT,
        "instruction": concept["question"],
        "response": concept["answer"]
    } for concept in all_concepts]

def generate_error_examples() -> List[Dict]:
    examples = []
    for scenario in ERROR_SCENARIOS:
        response = scenario["response"].copy()
        response["error_type"] = scenario["error_type"]
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": scenario["instruction"],
            "response": format_error_response(response)
        })
    return examples

def main():
    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(exist_ok=True)
    
    print("=" * 60)
    print("Generating .NET Development Training Data")
    print("=" * 60)
    
    all_examples = []
    
    tool_examples = generate_tool_examples()
    all_examples.extend(tool_examples)
    print(f"Generated {len(tool_examples)} CLI examples")
    
    code_examples = generate_code_examples()
    all_examples.extend(code_examples)
    print(f"Generated {len(code_examples)} code examples")
    
    planning_examples = generate_planning_examples()
    all_examples.extend(planning_examples)
    print(f"Generated {len(planning_examples)} planning examples")
    
    concept_examples = generate_concept_examples()
    all_examples.extend(concept_examples)
    print(f"Generated {len(concept_examples)} concept examples")
    
    error_examples = generate_error_examples()
    all_examples.extend(error_examples)
    print(f"Generated {len(error_examples)} error examples")
    
    random.shuffle(all_examples)
    
    output_file = output_dir / "dotnet.jsonl"
    with open(output_file, "w", encoding="utf-8") as f:
        for example in all_examples:
            f.write(json.dumps(example, ensure_ascii=False) + "\n")
    
    print(f"\nSaved {len(all_examples)} examples to {output_file}")

if __name__ == "__main__":
    main()
