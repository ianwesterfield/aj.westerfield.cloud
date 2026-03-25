using AJ.Orchestrator.Abstractions.Services;
using AJ.Orchestrator.Services;

var builder = WebApplication.CreateBuilder(args);

// Configuration
builder.Services.AddOptions();

// HTTP clients for external services
builder.Services.AddHttpClient("ollama", c =>
{
    c.BaseAddress = new Uri(builder.Configuration["Ollama:Url"] ?? "http://localhost:11434");
    c.Timeout = TimeSpan.FromMinutes(5);
});

builder.Services.AddHttpClient("pragmatics", c =>
{
    c.BaseAddress = new Uri(builder.Configuration["Pragmatics:Url"] ?? "http://localhost:8091");
});

builder.Services.AddHttpClient("funnel", c =>
{
    c.BaseAddress = new Uri(builder.Configuration["FunnelCloud:Url"] ?? "http://localhost:41421");
});

// Core services
builder.Services.AddSingleton<SessionStateManager>();
builder.Services.AddSingleton<IAgentDiscovery, AgentDiscoveryService>();
builder.Services.AddSingleton<IGrpcAgentClient, GrpcAgentClient>();
builder.Services.AddScoped<ITaskPlanner, TaskPlanner>();
builder.Services.AddScoped<IReasoningEngine, ReasoningEngine>();

// Controllers & API
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

// CORS for Open-WebUI integration
builder.Services.AddCors(options =>
{
    options.AddDefaultPolicy(policy =>
    {
        policy.AllowAnyOrigin()
              .AllowAnyHeader()
              .AllowAnyMethod();
    });
});

var app = builder.Build();

// Configure the HTTP request pipeline
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseCors();
app.MapControllers();

// Health endpoint
app.MapGet("/health", () => Results.Ok(new { status = "healthy", service = "orchestrator-dotnet" }));

Console.WriteLine("AJ Orchestrator (.NET) starting on port 8080...");
app.Run("http://0.0.0.0:8080");
