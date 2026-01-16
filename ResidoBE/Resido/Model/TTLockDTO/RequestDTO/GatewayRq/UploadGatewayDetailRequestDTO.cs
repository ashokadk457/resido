namespace Resido.Model.TTLockDTO.RequestDTO.GatewayRq
{
    /// <summary>
    /// Client-facing request DTO (no access token).
    /// </summary>
    public class UploadGatewayDetailRequestDTO
    {
        /// <summary>
        /// Gateway ID, returned by Gateway init.
        /// </summary>
        public int GatewayId { get; set; }

        /// <summary>
        /// Product model number.
        /// </summary>
        public string ModelNum { get; set; }

        /// <summary>
        /// Hardware version.
        /// </summary>
        public string HardwareRevision { get; set; }

        /// <summary>
        /// Firmware version.
        /// </summary>
        public string FirmwareRevision { get; set; }

        /// <summary>
        /// Network name the gateway is connected to.
        /// </summary>
        public string NetworkName { get; set; }
    }

    /// <summary>
    /// TTLock API request DTO (includes access token, clientId, date).
    /// </summary>
    public class TTLockUploadGatewayDetailRequestDTO : BaseRequestDTO, IAccessTokenRequest
    {
        public int GatewayId { get; set; }
        public string ModelNum { get; set; }
        public string HardwareRevision { get; set; }
        public string FirmwareRevision { get; set; }
        public string NetworkName { get; set; }
        public string AccessToken { get; set; }
    }
}
