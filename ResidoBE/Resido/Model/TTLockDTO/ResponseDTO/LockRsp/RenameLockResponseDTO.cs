namespace Resido.Model.TTLockDTO.ResponseDTO.LockRsp
{
    /// <summary>
    /// TTLock API response for rename lock.
    /// </summary>
    public class RenameLockResponseDTO : ITTLockErrorResponse
    {
        public int Errcode { get; set; }
        public string Errmsg { get; set; }
    }

}
