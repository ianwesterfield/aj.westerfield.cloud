namespace FunnelCloud.Agent;

/// <summary>
/// Trust constants embedded at build time.
/// DO NOT modify manually - regenerate certificates using scripts/New-CACertificate.ps1
/// </summary>
public static class TrustConfig
{
  /// <summary>
  /// SHA256 fingerprint of the FunnelCloud CA certificate.
  /// Used for certificate pinning - agents will only trust orchestrators
  /// presenting certificates signed by this CA.
  /// </summary>
  public const string CaFingerprint = "SHA256:1584BAFABC7E459886BCB1705AA8788442DB8A7D996F51D11D957D7E372B230F";

  /// <summary>
  /// Default password for PFX certificate files.
  /// In production, this should come from environment variable FUNNEL_CERT_PASSWORD.
  /// </summary>
  public const string DefaultCertPassword = "funnelcloud";

  /// <summary>
  /// UDP port for agent discovery broadcasts.
  /// </summary>
  public const int DiscoveryPort = 41234;

  /// <summary>
  /// gRPC port for task execution (mTLS).
  /// </summary>
  public const int GrpcPort = 41235;

  /// <summary>
  /// Magic string for discovery protocol identification.
  /// </summary>
  public const string DiscoveryMagic = "FUNNEL_DISCOVER";
}
