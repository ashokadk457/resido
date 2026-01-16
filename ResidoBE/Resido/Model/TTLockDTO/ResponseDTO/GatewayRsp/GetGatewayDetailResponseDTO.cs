namespace Resido.Model.TTLockDTO.ResponseDTO.GatewayRsp
{
    /// <summary>
    /// TTLock API response for gateway detail.
    /// </summary>
    public class GetGatewayDetailResponseDTO : ITTLockErrorResponse
    {
        public int GatewayId { get; set; }
        public string GatewayMac { get; set; }
        public string GatewayName { get; set; }
        public int GatewayVersion { get; set; }
        public string NetworkName { get; set; }
        public string NetworkMac { get; set; }
        public int LockNum { get; set; }
        public int IsOnline { get; set; }

        public int Errcode { get; set; }
        public string Errmsg { get; set; }
    }

}
