namespace Resido.Model.TTLockDTO.ResponseDTO.FingerPrintRsp
{
    /// <summary>
    /// TTLock API response for clear fingerprint.
    /// </summary>
    public class ClearFingerprintResponseDTO : ITTLockErrorResponse
    {
        public int Errcode { get; set; }
        public string Errmsg { get; set; }
    }

}
