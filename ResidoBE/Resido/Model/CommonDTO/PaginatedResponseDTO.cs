namespace Resido.Model.CommonDTO
{
    public class PaginatedResponseDTO<T>
    {
        public List<T> Data { get; set; } = new();
        public int PageNo { get; set; }
        public int PageSize { get; set; }
        public int TotalPages { get; set; }
        public int TotalRecords { get; set; }
        public string? Message { get; set; }
        public bool IsSuccess { get; set; } = true;

        public PaginatedResponseDTO<T> SetMessage(string message, bool isSuccess = false)
        {
            Message = message;
            IsSuccess = isSuccess;
            return this;
        }
    }
}
