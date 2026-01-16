namespace Resido.Model.TTLockDTO.RequestDTO.GatewayRq
{
    /// <summary>
    /// Client-facing request DTO (no access token).
    /// </summary>
    public class RenameGatewayRequestDTO
    {
        /// <summary>
        /// Gateway ID to rename.
        /// </summary>
        public int GatewayId { get; set; }

        /// <summary>
        /// New gateway name.
        /// </summary>
        public string GatewayName { get; set; }
    }

    /// <summary>
    /// TTLock API request DTO (includes access token, clientId, date).
    /// </summary>
    public class TTLockRenameGatewayRequestDTO : BaseRequestDTO, IAccessTokenRequest
    {
        public int GatewayId { get; set; }
        public string GatewayName { get; set; }
        public string AccessToken { get; set; }
    }
}
