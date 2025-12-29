namespace Resido.Model.TTLockDTO.RequestDTO
{
    /// <summary>
    /// Common paging request base class.
    /// </summary>
    public class PagingRequest
    {
        /// <summary>
        /// Page number, starting from 1
        /// </summary>
        public int PageNo { get; set; } = 1;

        /// <summary>
        /// Items per page, max 1000
        /// </summary>
        public int PageSize { get; set; } = 100;
    }

}
