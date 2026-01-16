namespace Resido.Model.TTLockDTO.ResponseDTO.GatewayRsp
{
    /// <summary>
    /// TTLock API response for update lock date.
    /// </summary>
    public class UpdateLockDateResponseDTO : ITTLockErrorResponse
    {
        /// <summary>
        /// The lock time after adjusting (timestamp in milliseconds).
        /// </summary>
        public long Date { get; set; }

        public int Errcode { get; set; }
        public string Errmsg { get; set; }
    }
}
