namespace Resido.Model.TTLockDTO.ResponseDTO.LockRsp
{
    /// <summary>
    /// TTLock API response for lock detail.
    /// </summary>
    public class GetLockDetailResponseDTO : ITTLockErrorResponse
    {
        public int LockId { get; set; }
        public string LockName { get; set; }
        public string LockAlias { get; set; }
        public string LockMac { get; set; }
        public string NoKeyPwd { get; set; }
        public int ElectricQuantity { get; set; }
        public string FeatureValue { get; set; }
        public long TimezoneRawOffset { get; set; }
        public string ModelNum { get; set; }
        public string HardwareRevision { get; set; }
        public string FirmwareRevision { get; set; }
        public int AutoLockTime { get; set; }
        public int LockSound { get; set; }
        public int SoundVolume { get; set; }
        public int HasGateway { get; set; }
        public int PrivacyLock { get; set; }
        public int TamperAlert { get; set; }
        public int ResetButton { get; set; }
        public int OpenDirection { get; set; }
        public int PassageMode { get; set; }
        public int PassageModeAutoUnlock { get; set; }
        public long Date { get; set; }

        public int EkeyLimitCount { get; set; }
        public int PinCodeLimitCount { get; set; }
        public int CardLimitCount { get; set; }
        public int FingerprintLimitCount { get; set; }
        public int EkeyCount { get; set; }
        public int PinCodeCount { get; set; }
        public int CardCount { get; set; }
        public int FingerprintCount { get; set; }
        public int Errcode { get; set; }
        public string Errmsg { get; set; }
    }
}
