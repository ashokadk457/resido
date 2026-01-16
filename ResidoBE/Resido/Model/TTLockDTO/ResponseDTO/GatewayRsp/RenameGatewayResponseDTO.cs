namespace Resido.Model.TTLockDTO.ResponseDTO.GatewayRsp
{
    /// <summary>
    /// TTLock API response for rename gateway.
    /// </summary>
    public class RenameGatewayResponseDTO : ITTLockErrorResponse
    {
        public int Errcode { get; set; }
        public string Errmsg { get; set; }
    }
}
