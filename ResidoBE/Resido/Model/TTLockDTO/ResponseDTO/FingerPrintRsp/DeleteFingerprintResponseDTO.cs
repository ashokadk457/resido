namespace Resido.Model.TTLockDTO.ResponseDTO.FingerPrintRsp
{
    /// <summary>
    /// TTLock API response for delete fingerprint.
    /// </summary>
    public class DeleteFingerprintResponseDTO : ITTLockErrorResponse
    {
        public int Errcode { get; set; }
        public string Errmsg { get; set; }
    }
}
