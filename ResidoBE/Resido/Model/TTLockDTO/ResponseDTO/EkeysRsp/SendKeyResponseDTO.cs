namespace Resido.Model.TTLockDTO.ResponseDTO.EkeysRsp
{
    /// <summary>
    /// TTLock API response for send ekey.
    /// </summary>
    public class SendKeyResponseDTO : ITTLockErrorResponse
    {
        public int Errcode { get; set; }
        public string Errmsg { get; set; }

        /// <summary>
        /// Ekey ID returned when successfully sent
        /// </summary>
        public int KeyId { get; set; }
    }
}
