namespace Resido.Model.TTLockDTO.ResponseDTO.GatewayRsp
{
    /// <summary>
    /// Represents a single gateway record associated with a lock.
    /// </summary>
    public class GatewayByLockRecordDTO
    {
        public int GatewayId { get; set; }
        public string GatewayMac { get; set; }
        public string GatewayName { get; set; }
        public int Rssi { get; set; }
        public long RssiUpdateDate { get; set; }

        /// <summary>
        /// Human-friendly RSSI label (Strong/Medium/Weak).
        /// </summary>
        public string RssiStrength
        {
            get
            {
                if (Rssi > -75) return "Strong";
                if (Rssi > -85) return "Medium";
                return "Weak";
            }
        }
    }

    /// <summary>
    /// TTLock API response for list gateways by lock.
    /// </summary>
    public class ListGatewaysByLockResponseDTO : ITTLockErrorResponse
    {
        public List<GatewayByLockRecordDTO> List { get; set; }
        public int Errcode { get; set; }
        public string Errmsg { get; set; }
    }
}
