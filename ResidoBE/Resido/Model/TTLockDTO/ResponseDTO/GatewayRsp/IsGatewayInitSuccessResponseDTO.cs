namespace Resido.Model.TTLockDTO.ResponseDTO.GatewayRsp
{
    /// <summary>
    /// TTLock API response for gateway init success.
    /// </summary>
    public class IsGatewayInitSuccessResponseDTO : ITTLockErrorResponse
    {
        /// <summary>
        /// Gateway ID if initialization succeeded.
        /// </summary>
        public int GatewayId { get; set; }

        public int Errcode { get; set; }
        public string Errmsg { get; set; }
    }
}
