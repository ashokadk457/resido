namespace Resido.Model.TTLockDTO.ResponseDTO.LockRsp
{
    /// <summary>
    /// TTLock API response for lock initialization.
    /// </summary>
    public class InitializeLockResponseDTO : ITTLockErrorResponse
    {
        /// <summary>
        /// Lock ID generated after initialization.
        /// </summary>
        public int LockId { get; set; }

        /// <summary>
        /// Admin eKey ID generated for the user.
        /// </summary>
        public int KeyId { get; set; }

        public int Errcode { get; set; }
        public string Errmsg { get; set; }
    }

}
