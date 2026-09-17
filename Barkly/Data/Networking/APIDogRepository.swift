import Foundation

struct APIDogRepository: DogRepository {
    private let client: APIClient

    init(client: APIClient) {
        self.client = client
    }

    func fetchDogs() async throws -> [Dog] {
        do {
            let dogs: [DogDTO] = try await client.get("api/v1/dogs")
            return dogs.map(Dog.init(dto:))
        } catch let error as APIClientError {
            throw Self.map(error)
        }
    }

    func fetchDog(id: UUID) async throws -> Dog? {
        do {
            let dog: DogDTO = try await client.get("api/v1/dogs/\(id.uuidString)")
            return Dog(dto: dog)
        } catch let error as APIClientError {
            if case .http(let status, _, _) = error, status == 404 {
                return nil
            }
            throw Self.map(error)
        }
    }

    func updateDog(_ dog: Dog) async throws -> Dog {
        let body = DogCreateDTO(
            name: dog.name,
            breed: dog.breed.isEmpty ? nil : dog.breed,
            sex: nil,
            dateOfBirth: dog.dateOfBirth,
            notes: dog.notes
        )
        do {
            let updated: DogDTO = try await client.patch("api/v1/dogs/\(dog.id.uuidString)", body: body)
            return Dog(dto: updated)
        } catch let error as APIClientError {
            throw Self.map(error)
        }
    }

    func createDog(name: String, breed: String?, dateOfBirth: Date, notes: String?) async throws -> Dog {
        let body = DogCreateDTO(
            name: name,
            breed: breed,
            sex: nil,
            dateOfBirth: dateOfBirth,
            notes: notes
        )
        do {
            let dog: DogDTO = try await client.post("api/v1/dogs", body: body)
            return Dog(dto: dog)
        } catch let error as APIClientError {
            throw Self.map(error)
        }
    }

    func deleteDog(id: UUID) async throws {
        do {
            try await client.delete("api/v1/dogs/\(id.uuidString)")
        } catch let error as APIClientError {
            throw Self.map(error)
        }
    }

    private static func map(_ error: APIClientError) -> Error {
        switch error {
        case .unauthorized:
            return AppRepositoryError.unauthorized
        case .http(let status, _, _):
            return status == 401 ? AppRepositoryError.unauthorized : AppRepositoryError.serviceUnavailable
        case .transport:
            return AppRepositoryError.offline
        case .decoding, .invalidRequest:
            return AppRepositoryError.invalidData
        }
    }
}