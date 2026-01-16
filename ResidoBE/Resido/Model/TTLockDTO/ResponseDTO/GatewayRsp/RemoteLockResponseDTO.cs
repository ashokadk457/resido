namespace Resido.Model.TTLockDTO.ResponseDTO.GatewayRsp
{
    /// <summary>
    /// TTLock API response for remote lock.
    /// </summary>
    public class RemoteLockResponseDTO : ITTLockErrorResponse
    {
        public int Errcode { get; set; }
        public string Errmsg { get; set; }
    }
}
