namespace Resido.Model.TTLockDTO.ResponseDTO.FingerPrintRsp
{
    /// <summary>
    /// TTLock API response for rename fingerprint.
    /// </summary>
    public class RenameFingerprintResponseDTO : ITTLockErrorResponse
    {
        public int Errcode { get; set; }
        public string Errmsg { get; set; }
    }
}
