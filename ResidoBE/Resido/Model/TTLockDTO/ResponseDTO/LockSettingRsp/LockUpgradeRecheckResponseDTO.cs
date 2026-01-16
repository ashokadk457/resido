namespace Resido.Model.TTLockDTO.ResponseDTO.LockSettingRsp
{

    /// <summary>
    /// TTLock API response for lock upgrade recheck.
    /// </summary>
    public class LockUpgradeRecheckResponseDTO : ITTLockErrorResponse
    {
        /// <summary>
        /// Upgrade availability: 0 = No, 1 = Yes, 2 = Unknown.
        /// </summary>
        public int NeedUpgrade { get; set; }

        /// <summary>
        /// Lock firmware info.
        /// </summary>
        public LockFirmwareInfoDTO FirmwareInfo { get; set; }

        /// <summary>
        /// Firmware package (encoded string).
        /// </summary>
        public string FirmwarePackage { get; set; }

        /// <summary>
        /// Latest firmware version available.
        /// </summary>
        public string Version { get; set; }

        public int Errcode { get; set; }
        public string Errmsg { get; set; }
    }

}
