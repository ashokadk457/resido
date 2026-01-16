namespace Resido.Model.TTLockDTO.ResponseDTO.GatewayRsp
{
    /// <summary>
    /// Firmware info returned by TTLock API.
    /// </summary>
    public class GatewayFirmwareInfoDTO
    {
        public string ModelNum { get; set; }
        public string HardwareRevision { get; set; }
        public string FirmwareRevision { get; set; }
    }

    /// <summary>
    /// TTLock API response for gateway upgrade check.
    /// </summary>
    public class GatewayUpgradeCheckResponseDTO : ITTLockErrorResponse
    {
        /// <summary>
        /// Upgrade availability: 0 = No, 1 = Yes, 2 = Unknown.
        /// </summary>
        public int NeedUpgrade { get; set; }

        /// <summary>
        /// Firmware info (model, hardware, firmware).
        /// </summary>
        public GatewayFirmwareInfoDTO FirmwareInfo { get; set; }

        /// <summary>
        /// Latest firmware version available.
        /// </summary>
        public string Version { get; set; }

        public int Errcode { get; set; }
        public string Errmsg { get; set; }
    }
}
