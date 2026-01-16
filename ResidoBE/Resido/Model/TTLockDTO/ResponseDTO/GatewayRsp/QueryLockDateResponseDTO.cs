namespace Resido.Model.TTLockDTO.ResponseDTO.GatewayRsp
{
    /// <summary>
    /// TTLock API response for query lock date.
    /// </summary>
    public class QueryLockDateResponseDTO : ITTLockErrorResponse
    {
        /// <summary>
        /// Lock time (timestamp in milliseconds).
        /// </summary>
        public long Date { get; set; }

        public int Errcode { get; set; }
        public string Errmsg { get; set; }
    }

}
