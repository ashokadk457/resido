namespace Resido.Model.TTLockDTO.ResponseDTO.LockRsp
{
    /// <summary>
    /// TTLock API response for delete lock.
    /// </summary>
    public class DeleteLockResponseDTO : ITTLockErrorResponse
    {
        public int Errcode { get; set; }
        public string Errmsg { get; set; }
    }
}
