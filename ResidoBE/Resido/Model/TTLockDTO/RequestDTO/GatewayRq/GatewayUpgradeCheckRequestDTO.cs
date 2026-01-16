namespace Resido.Model.TTLockDTO.RequestDTO.GatewayRq
{
    /// <summary>
    /// Client-facing request DTO (no access token).
    /// </summary>
    public class GatewayRequestDTO
    {
        /// <summary>
        /// Gateway ID to check for firmware upgrade.
        /// </summary>
        public int GatewayId { get; set; }
    }

    /// <summary>
    /// TTLock API request DTO (includes access token, clientId, date).
    /// </summary>
    public class TTLockGatewayUpgradeCheckRequestDTO : BaseRequestDTO, IAccessTokenRequest
    {
        public int GatewayId { get; set; }
        public string AccessToken { get; set; }
    }
}
