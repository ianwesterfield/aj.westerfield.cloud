# Build stage
FROM mcr.microsoft.com/dotnet/sdk:9.0 AS build
WORKDIR /src

# Copy project files
COPY AJ.Orchestrator/*.csproj AJ.Orchestrator/
COPY AJ.Shared/*.csproj AJ.Shared/

# Restore dependencies
RUN dotnet restore AJ.Orchestrator/AJ.Orchestrator.csproj

# Copy source code
COPY AJ.Orchestrator/ AJ.Orchestrator/
COPY AJ.Shared/ AJ.Shared/

# Build and publish
WORKDIR /src/AJ.Orchestrator
RUN dotnet publish -c Release -o /app/publish

# Runtime stage
FROM mcr.microsoft.com/dotnet/aspnet:9.0-alpine AS runtime
WORKDIR /app

# Install ICU for globalization support
RUN apk add --no-cache icu-libs

ENV DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=false
ENV ASPNETCORE_URLS=http://+:8080
ENV ASPNETCORE_ENVIRONMENT=Production

# Copy published output
COPY --from=build /app/publish .

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1

EXPOSE 8080

ENTRYPOINT ["dotnet", "AJ.Orchestrator.dll"]