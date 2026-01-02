using System.Net;
using System.Security.Cryptography;
using System.Security.Cryptography.X509Certificates;
using FunnelCloud.Shared.Contracts;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Server.Kestrel.Core;
using Microsoft.AspNetCore.Server.Kestrel.Https;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;

namespace FunnelCloud.Agent.Services;

/// <summary>
/// Hosts the gRPC server with mTLS authentication.
/// 
/// Security model:
/// 1. Server presents certificate signed by FunnelCloud CA
/// 2. Client (orchestrator) must present certificate signed by same CA
/// 3. Both sides validate certificate chain against pinned CA fingerprint
/// </summary>
public class GrpcServerHost : BackgroundService
{
  private readonly ILogger<GrpcServerHost> _logger;
  private readonly AgentCapabilities _capabilities;
  private readonly TaskExecutor _executor;
  private readonly int _port;
  private IHost? _host;

  public GrpcServerHost(
      ILogger<GrpcServerHost> logger,
      AgentCapabilities capabilities,
      TaskExecutor executor,
      int? port = null)
  {
    _logger = logger;
    _capabilities = capabilities;
    _executor = executor;
    _port = port ?? TrustConfig.GrpcPort;
  }

  protected override async Task ExecuteAsync(CancellationToken stoppingToken)
  {
    _logger.LogInformation("Starting gRPC server on port {Port}", _port);

    try
    {
      // Load agent certificate
      var certPath = Environment.GetEnvironmentVariable("FUNNEL_CERT_PATH");
      var certPassword = Environment.GetEnvironmentVariable("FUNNEL_CERT_PASSWORD")
          ?? TrustConfig.DefaultCertPassword;

      if (string.IsNullOrEmpty(certPath))
      {
        // Try default location
        certPath = Path.Combine(
            AppContext.BaseDirectory,
            "..", "..", "..", "..", "certs", "agents",
            _capabilities.AgentId ?? "dev-workstation",
            "agent.pfx");

        if (!File.Exists(certPath))
        {
          _logger.LogWarning(
              "No certificate found. Set FUNNEL_CERT_PATH or run New-AgentCertificate.ps1. " +
              "Starting in INSECURE mode (no mTLS).");
          await RunInsecure(stoppingToken);
          return;
        }
      }

      var certificate = LoadCertificate(certPath, certPassword);
      if (certificate == null)
      {
        _logger.LogError("Failed to load certificate from {Path}", certPath);
        return;
      }

      _logger.LogInformation("Loaded certificate: {Subject}", certificate.Subject);

      // Build and run the gRPC host
      _host = CreateHostBuilder(certificate).Build();
      await _host.RunAsync(stoppingToken);
    }
    catch (OperationCanceledException) when (stoppingToken.IsCancellationRequested)
    {
      _logger.LogInformation("gRPC server shutting down");
    }
    catch (Exception ex)
    {
      _logger.LogError(ex, "gRPC server failed");
      throw;
    }
  }

  private async Task RunInsecure(CancellationToken stoppingToken)
  {
    _logger.LogWarning("Running gRPC server WITHOUT mTLS - for development only!");

    var builder = WebApplication.CreateBuilder();

    builder.Services.AddGrpc();
    builder.Services.AddSingleton(_capabilities);
    builder.Services.AddSingleton(_executor);
    builder.Services.AddSingleton<TaskServiceImpl>();

    builder.WebHost.ConfigureKestrel(options =>
    {
      options.Listen(IPAddress.Any, _port, listenOptions =>
          {
          listenOptions.Protocols = HttpProtocols.Http2;
        });
    });

    var app = builder.Build();
    app.MapGrpcService<TaskServiceImpl>();

    _logger.LogInformation("gRPC server (INSECURE) listening on port {Port}", _port);
    await app.RunAsync(stoppingToken);
  }

  private IHostBuilder CreateHostBuilder(X509Certificate2 serverCertificate)
  {
    return Host.CreateDefaultBuilder()
        .ConfigureWebHostDefaults(webBuilder =>
        {
          webBuilder.ConfigureKestrel(options =>
              {
              options.Listen(IPAddress.Any, _port, listenOptions =>
                  {
                  listenOptions.Protocols = HttpProtocols.Http2;
                  listenOptions.UseHttps(httpsOptions =>
                      {
                      httpsOptions.ServerCertificate = serverCertificate;
                      httpsOptions.ClientCertificateMode = ClientCertificateMode.RequireCertificate;
                      httpsOptions.ClientCertificateValidation = ValidateClientCertificate;
                    });
                });
            });

          webBuilder.ConfigureServices(services =>
              {
              services.AddGrpc();
              services.AddSingleton(_capabilities);
              services.AddSingleton(_executor);
              services.AddSingleton<TaskServiceImpl>();
            });

          webBuilder.Configure(app =>
              {
              app.UseRouting();
              app.UseEndpoints(endpoints =>
                  {
                  endpoints.MapGrpcService<TaskServiceImpl>();
                });
            });
        });
  }

  private bool ValidateClientCertificate(
      X509Certificate2 certificate,
      X509Chain? chain,
      System.Net.Security.SslPolicyErrors sslPolicyErrors)
  {
    _logger.LogDebug("Validating client certificate: {Subject}", certificate.Subject);

    // In production, we verify the certificate was signed by our CA
    // by checking the CA fingerprint matches our pinned value

    if (chain == null || chain.ChainElements.Count < 2)
    {
      _logger.LogWarning("Client certificate chain is incomplete");
      return false;
    }

    // Get the issuer (CA) certificate
    var issuerCert = chain.ChainElements[^1].Certificate;
    var issuerFingerprint = ComputeSha256Fingerprint(issuerCert);

    _logger.LogDebug("Client cert issuer fingerprint: {Fingerprint}", issuerFingerprint);
    _logger.LogDebug("Expected CA fingerprint: {Expected}", TrustConfig.CaFingerprint);

    if (!string.Equals(issuerFingerprint, TrustConfig.CaFingerprint, StringComparison.OrdinalIgnoreCase))
    {
      _logger.LogWarning(
          "Client certificate not signed by trusted CA. Expected: {Expected}, Got: {Actual}",
          TrustConfig.CaFingerprint, issuerFingerprint);
      return false;
    }

    // Verify certificate is not expired
    var now = DateTime.UtcNow;
    if (certificate.NotBefore > now || certificate.NotAfter < now)
    {
      _logger.LogWarning("Client certificate is expired or not yet valid");
      return false;
    }

    _logger.LogInformation("Client certificate validated: {Subject}", certificate.Subject);
    return true;
  }

  private static string ComputeSha256Fingerprint(X509Certificate2 certificate)
  {
    using var sha256 = SHA256.Create();
    var certBytes = certificate.Export(X509ContentType.Cert);
    var hashBytes = sha256.ComputeHash(certBytes);
    return "SHA256:" + BitConverter.ToString(hashBytes).Replace("-", "");
  }

  private X509Certificate2? LoadCertificate(string path, string password)
  {
    try
    {
      return new X509Certificate2(
          path,
          password,
          X509KeyStorageFlags.Exportable | X509KeyStorageFlags.PersistKeySet);
    }
    catch (Exception ex)
    {
      _logger.LogError(ex, "Failed to load certificate from {Path}", path);
      return null;
    }
  }

  public override async Task StopAsync(CancellationToken cancellationToken)
  {
    _logger.LogInformation("Stopping gRPC server");

    if (_host != null)
    {
      await _host.StopAsync(cancellationToken);
      _host.Dispose();
    }

    await base.StopAsync(cancellationToken);
  }
}
