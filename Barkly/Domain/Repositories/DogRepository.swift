import Foundation

protocol DogRepository: Sendable {
    func fetchDogs() async throws -> [Dog]
    func fetchDog(id: UUID) async throws -> Dog?
    func updateDog(_ dog: Dog) async throws -> Dog
    func createDog(name: String, breed: String?, dateOfBirth: Date, notes: String?) async throws -> Dog
}