namespace Resido.Model.TTLockDTO.ResponseDTO.GatewayRsp
{
    /// <summary>
    /// TTLock API response for delete gateway.
    /// </summary>
    public class DeleteGatewayResponseDTO : ITTLockErrorResponse
    {
        public int Errcode { get; set; }
        public string Errmsg { get; set; }
    }
}
