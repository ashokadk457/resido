namespace Resido.Model.TTLockDTO.ResponseDTO.LockRsp
{
    /// <summary>
    /// TTLock API response for set auto lock time.
    /// </summary>
    public class SetAutoLockTimeResponseDTO : ITTLockErrorResponse
    {
        public int Errcode { get; set; }
        public string Errmsg { get; set; }
    }

}
