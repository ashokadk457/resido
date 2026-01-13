namespace Resido.Model.TTLockDTO.ResponseDTO.FingerPrintRsp
{
    /// <summary>
    /// TTLock API response for add fingerprint.
    /// </summary>
    public class AddFingerprintResponseDTO : ITTLockErrorResponse
    {
        /// <summary>
        /// Fingerprint ID generated after adding.
        /// </summary>
        public int FingerprintId { get; set; }

        public int Errcode { get; set; }
        public string Errmsg { get; set; }
    }
}
