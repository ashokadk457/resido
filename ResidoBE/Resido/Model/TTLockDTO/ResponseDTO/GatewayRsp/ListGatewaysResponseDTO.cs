namespace Resido.Model.TTLockDTO.ResponseDTO.GatewayRsp
{
    /// <summary>
    /// Represents a single gateway record.
    /// </summary>
    public class GatewayRecordDTO
    {
        public int GatewayId { get; set; }
        public string GatewayMac { get; set; }
        public string GatewayName { get; set; }
        public int GatewayVersion { get; set; }
        public string NetworkName { get; set; }
        public string NetworkMac { get; set; }
        public int LockNum { get; set; }
        public int IsOnline { get; set; }
    }

    /// <summary>
    /// TTLock API response for list gateways.
    /// </summary>
    public class ListGatewaysResponseDTO : ResponseCodeDTO
    {
        public List<GatewayRecordDTO> List { get; set; }
        public int PageNo { get; set; }
        public int PageSize { get; set; }
        public int Pages { get; set; }
        public int Total { get; set; }
    }
}
