namespace Resido.Model.TTLockDTO.ResponseDTO.GatewayRsp
{
    /// <summary>
    /// Represents a single lock record associated with a gateway.
    /// </summary>
    public class GatewayLockRecordDTO
    {
        public int LockId { get; set; }
        public string LockMac { get; set; }
        public string LockName { get; set; }
        public string LockAlias { get; set; }
        public int Rssi { get; set; }
        public long UpdateDate { get; set; }
    }

    /// <summary>
    /// TTLock API response for list locks of a gateway.
    /// </summary>
    public class ListGatewayLocksResponseDTO : ITTLockErrorResponse
    {
        public List<GatewayLockRecordDTO> List { get; set; }
        public int Errcode { get; set; }
        public string Errmsg { get; set; }
    }
}
